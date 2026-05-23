import re
import secrets
import string
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import raise_auth_error
from app.platform.models import CodeType, PlatformCode, PlatformSettings, RegistrationMode
from app.platform.registration import normalize_registration_mode, registration_invite_required

ERR_REGISTRATION_CLOSED = 40303
ERR_INVALID_INVITE_CODE = 40304
ERR_INVITE_CODE_EXPIRED = 40305
ERR_INVITE_CODE_USED = 40306
ERR_INVALID_RECHARGE_CODE = 40307
ERR_RECHARGE_CODE_EXPIRED = 40308
ERR_RECHARGE_CODE_USED = 40309
ERR_RECHARGE_VALUE_INVALID = 48004

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def normalize_code(raw: str | None) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"[\s\-_]+", "", raw.strip().upper())
    return cleaned


def _generate_code(length: int = 10) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


async def _code_exists(db: AsyncSession, code: str) -> bool:
    result = await db.execute(select(PlatformCode.id).where(PlatformCode.code == code).limit(1))
    return result.scalar_one_or_none() is not None


async def _unique_code(db: AsyncSession, length: int = 10) -> str:
    for _ in range(32):
        candidate = _generate_code(length)
        if not await _code_exists(db, candidate):
            return candidate
    raise RuntimeError("failed to generate unique code")


async def assert_registration_allowed(
    db: AsyncSession,
    settings: PlatformSettings,
    *,
    invite_code: str | None,
) -> PlatformCode | None:
    mode = normalize_registration_mode(settings.registration_mode)

    if mode == RegistrationMode.CLOSED:
        raise_auth_error(
            code=ERR_REGISTRATION_CLOSED,
            message="registration is closed",
            http_status=403,
        )

    if not registration_invite_required(settings):
        return None

    return await _lock_valid_code(
        db,
        code_str=invite_code,
        code_type=CodeType.INVITE,
        invalid_code=ERR_INVALID_INVITE_CODE,
        expired_code=ERR_INVITE_CODE_EXPIRED,
        used_code=ERR_INVITE_CODE_USED,
        missing_message="invite code is required",
    )


async def _lock_valid_code(
    db: AsyncSession,
    *,
    code_str: str | None,
    code_type: str,
    invalid_code: int,
    expired_code: int,
    used_code: int,
    missing_message: str,
) -> PlatformCode:
    normalized = normalize_code(code_str)
    if not normalized:
        raise_auth_error(code=invalid_code, message=missing_message, http_status=403)

    result = await db.execute(
        select(PlatformCode)
        .where(
            PlatformCode.code == normalized,
            PlatformCode.code_type == code_type,
        )
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise_auth_error(code=invalid_code, message="invalid code", http_status=403)

    if row.used_at is not None:
        raise_auth_error(code=used_code, message="code already used", http_status=403)

    if row.expires_at is not None and row.expires_at <= datetime.now(UTC):
        raise_auth_error(code=expired_code, message="code expired", http_status=403)

    return row


async def consume_invite_code(db: AsyncSession, code: PlatformCode, user_id: UUID) -> None:
    code.used_at = datetime.now(UTC)
    code.used_by_id = user_id


async def redeem_recharge_code(
    db: AsyncSession,
    *,
    user_id: UUID,
    code_str: str,
) -> PlatformCode:
    code = await _lock_valid_code(
        db,
        code_str=code_str,
        code_type=CodeType.RECHARGE,
        invalid_code=ERR_INVALID_RECHARGE_CODE,
        expired_code=ERR_RECHARGE_CODE_EXPIRED,
        used_code=ERR_RECHARGE_CODE_USED,
        missing_message="recharge code is required",
    )
    if not code.value_cents or code.value_cents <= 0:
        raise_auth_error(
            code=ERR_RECHARGE_VALUE_INVALID,
            message="recharge code has no value",
            http_status=422,
        )
    code.used_at = datetime.now(UTC)
    code.used_by_id = user_id
    return code


async def generate_platform_codes(
    db: AsyncSession,
    *,
    admin_id: UUID,
    code_type: str,
    count: int,
    expires_at: datetime | None,
    value_cents: int | None = None,
) -> dict:
    if code_type not in (CodeType.INVITE, CodeType.RECHARGE):
        raise_auth_error(code=40001, message="invalid code type", http_status=400)
    if count < 1 or count > 500:
        raise_auth_error(code=40001, message="count must be between 1 and 500", http_status=400)
    if code_type == CodeType.RECHARGE and (value_cents is None or value_cents <= 0):
        raise_auth_error(code=40001, message="recharge codes require positive value_cents", http_status=400)
    if expires_at is not None and expires_at <= datetime.now(UTC):
        raise_auth_error(code=40001, message="expires_at must be in the future", http_status=400)

    batch_id = uuid4()
    created: list[str] = []
    for _ in range(count):
        code_value = await _unique_code(db)
        db.add(
            PlatformCode(
                code=code_value,
                code_type=code_type,
                value_cents=value_cents if code_type == CodeType.RECHARGE else None,
                expires_at=expires_at,
                batch_id=batch_id,
                created_by_id=admin_id,
            )
        )
        created.append(code_value)

    from app.platform.service import log_admin_action

    await log_admin_action(
        db,
        admin_id=admin_id,
        action="generate_platform_codes",
        target_type="platform_code_batch",
        target_id=str(batch_id),
        detail=f"type={code_type} count={count}",
    )
    await db.commit()
    return {
        "batch_id": str(batch_id),
        "code_type": code_type,
        "count": len(created),
        "codes": created,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "value_cents": value_cents,
    }


def _code_status(row: PlatformCode) -> str:
    if row.used_at is not None:
        return "used"
    if row.expires_at is not None and row.expires_at <= datetime.now(UTC):
        return "expired"
    return "active"


def _code_to_dict(row: PlatformCode) -> dict:
    return {
        "id": str(row.id),
        "code": row.code,
        "code_type": row.code_type,
        "value_cents": row.value_cents,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "used_at": row.used_at.isoformat() if row.used_at else None,
        "used_by_id": str(row.used_by_id) if row.used_by_id else None,
        "batch_id": str(row.batch_id),
        "status": _code_status(row),
        "created_at": row.created_at.isoformat(),
    }


async def list_platform_codes(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    code_type: str | None = None,
    status: str | None = None,
    batch_id: UUID | None = None,
) -> dict:
    query = select(PlatformCode)
    if code_type:
        query = query.where(PlatformCode.code_type == code_type)
    if batch_id:
        query = query.where(PlatformCode.batch_id == batch_id)

    rows = (await db.execute(query.order_by(PlatformCode.created_at.desc()))).scalars().all()
    if status:
        rows = [row for row in rows if _code_status(row) == status]

    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start : start + page_size]
    return {
        "items": [_code_to_dict(row) for row in page_rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
