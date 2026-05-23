import gzip
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.platform.models import BackupStatus, BackupTrigger, DatabaseBackup, PlatformSettings
from app.platform.service import get_or_create_settings, log_admin_action


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _backup_dir() -> Path:
    configured = (app_settings.BACKUP_DIR or "").strip()
    if configured:
        return Path(configured)
    return PROJECT_ROOT / "backups"


def _parse_database_url() -> dict[str, str | int]:
    raw = app_settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    raw = raw.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(raw)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "dbname": (parsed.path or "/").lstrip("/") or "capability_network",
    }


def _s3_configured(row: PlatformSettings) -> bool:
    return bool(
        row.backup_s3_endpoint
        and row.backup_s3_bucket
        and row.backup_s3_access_key
        and row.backup_s3_secret_key
    )


def _build_object_key(row: PlatformSettings, filename: str) -> str:
    prefix = (row.backup_s3_prefix or "backups/").strip("/")
    if prefix:
        return f"{prefix}/{filename}"
    return filename


def _serialize_backup(item: DatabaseBackup) -> dict:
    return {
        "id": str(item.id),
        "status": item.status,
        "filename": item.filename,
        "file_path": item.file_path,
        "object_key": item.object_key,
        "size_bytes": item.size_bytes,
        "trigger_type": item.trigger_type,
        "error_message": item.error_message,
        "started_at": item.started_at.isoformat(),
        "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        "created_by_admin_id": str(item.created_by_admin_id) if item.created_by_admin_id else None,
        "created_at": item.created_at.isoformat(),
    }


def _run_pg_dump(output_path: Path, params: dict[str, str | int]) -> None:
    env = os.environ.copy()
    env["PGPASSWORD"] = str(params["password"])
    cmd = [
        "pg_dump",
        "-h",
        str(params["host"]),
        "-p",
        str(params["port"]),
        "-U",
        str(params["user"]),
        "-d",
        str(params["dbname"]),
        "--no-owner",
        "--no-privileges",
    ]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", errors="replace").strip() or "pg_dump failed"
        raise RuntimeError(message)
    with gzip.open(output_path, "wb") as gz:
        gz.write(proc.stdout)


def _upload_to_s3(row: PlatformSettings, local_path: Path, object_key: str) -> None:
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=row.backup_s3_endpoint,
        region_name=row.backup_s3_region or "auto",
        aws_access_key_id=row.backup_s3_access_key,
        aws_secret_access_key=row.backup_s3_secret_key,
        config=Config(signature_version="s3v4"),
    )
    client.upload_file(str(local_path), row.backup_s3_bucket, object_key)


async def list_database_backups(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(DatabaseBackup)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(DatabaseBackup.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return {
        "items": [_serialize_backup(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def trigger_database_backup(
    db: AsyncSession,
    *,
    admin_id: UUID | None,
    dry_run: bool = False,
    trigger_type: str = BackupTrigger.MANUAL,
) -> dict:
    settings_row = await get_or_create_settings(db)
    params = _parse_database_url()
    started_at = datetime.now(UTC)
    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    filename = f"{params['dbname']}_{timestamp}.sql.gz"

    backup = DatabaseBackup(
        status=BackupStatus.RUNNING if not dry_run else BackupStatus.DRY_RUN,
        filename=filename,
        trigger_type=trigger_type,
        started_at=started_at,
        created_by_admin_id=admin_id,
    )
    db.add(backup)
    await db.flush()

    if dry_run:
        backup.finished_at = datetime.now(UTC)
        if admin_id is not None:
            await log_admin_action(
                db,
                admin_id=admin_id,
                action="backup_trigger",
                target_type="database_backup",
                target_id=str(backup.id),
                detail="dry_run",
            )
        await db.commit()
        await db.refresh(backup)
        return _serialize_backup(backup)

    backup_dir = _backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    output_path = backup_dir / filename
    backup.file_path = str(output_path)

    try:
        _run_pg_dump(output_path, params)
        backup.size_bytes = output_path.stat().st_size
        if _s3_configured(settings_row):
            object_key = _build_object_key(settings_row, filename)
            _upload_to_s3(settings_row, output_path, object_key)
            backup.object_key = object_key
        backup.status = BackupStatus.COMPLETED
        backup.finished_at = datetime.now(UTC)
        if admin_id is not None:
            await log_admin_action(
                db,
                admin_id=admin_id,
                action="backup_trigger",
                target_type="database_backup",
                target_id=str(backup.id),
                detail=filename,
            )
        await db.commit()
    except Exception as exc:
        backup.status = BackupStatus.FAILED
        backup.error_message = str(exc)[:2000]
        backup.finished_at = datetime.now(UTC)
        if admin_id is not None:
            await log_admin_action(
                db,
                admin_id=admin_id,
                action="backup_trigger_failed",
                target_type="database_backup",
                target_id=str(backup.id),
                detail=backup.error_message,
            )
        await db.commit()
        await db.refresh(backup)
        return _serialize_backup(backup)

    await db.refresh(backup)
    return _serialize_backup(backup)
