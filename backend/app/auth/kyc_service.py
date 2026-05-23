from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import (
    ERR_KYC_ALREADY_VERIFIED,
    ERR_KYC_ID_DUPLICATE,
    ERR_KYC_INVALID,
    ERR_KYC_NOT_FOUND,
    ERR_KYC_PENDING,
    KycLevel,
    UserStatus,
)
from app.auth.kyc_crypto import (
    decrypt_id_number,
    encrypt_id_number,
    hash_id_number,
    is_valid_id_number,
    is_valid_real_name,
    mask_id_number,
    normalize_id_number,
)
from app.auth.models import User
from app.auth.schemas import KycStatusInfo, raise_auth_error
from app.platform.service import log_admin_action


def derive_kyc_status(user: User) -> str:
    if user.kyc_level in (KycLevel.L1, KycLevel.L2):
        return "verified"
    if user.kyc_real_name and user.kyc_id_number:
        return "pending"
    return "none"


def kyc_status_for_user(user: User) -> KycStatusInfo:
    status = derive_kyc_status(user)
    masked = None
    if user.kyc_id_number and status in ("pending", "verified"):
        try:
            masked = mask_id_number(decrypt_id_number(user.kyc_id_number))
        except Exception:
            masked = None
    return KycStatusInfo(
        kyc_level=KycLevel(user.kyc_level),
        kyc_status=status,
        kyc_real_name=user.kyc_real_name,
        kyc_id_number_masked=masked,
    )


async def submit_kyc(
    db: AsyncSession,
    *,
    user_id: UUID,
    real_name: str,
    id_number: str,
) -> KycStatusInfo:
    name = real_name.strip()
    if not is_valid_real_name(name):
        raise_auth_error(code=ERR_KYC_INVALID, message="invalid real name format", http_status=422)

    normalized_id = normalize_id_number(id_number)
    if not is_valid_id_number(normalized_id):
        raise_auth_error(code=ERR_KYC_INVALID, message="invalid id number format", http_status=422)

    user = await db.get(User, user_id)
    if user is None:
        raise_auth_error(code=40401, message="user not found", http_status=404)

    if user.kyc_level in (KycLevel.L1, KycLevel.L2):
        raise_auth_error(code=ERR_KYC_ALREADY_VERIFIED, message="kyc already verified", http_status=409)

    if derive_kyc_status(user) == "pending":
        raise_auth_error(code=ERR_KYC_PENDING, message="kyc submission already pending review", http_status=409)

    id_hash = hash_id_number(normalized_id)
    duplicate = await db.execute(
        select(User.id).where(
            User.kyc_id_number_hash == id_hash,
            User.id != user_id,
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise_auth_error(code=ERR_KYC_ID_DUPLICATE, message="id number already registered", http_status=409)

    user.kyc_real_name = name
    user.kyc_id_number = encrypt_id_number(normalized_id)
    user.kyc_id_number_hash = id_hash
    await db.commit()
    await db.refresh(user)
    return kyc_status_for_user(user)


async def list_kyc_submissions(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
) -> dict:
    query = select(User).where(User.status != UserStatus.DELETED)
    count_query = select(func.count()).select_from(User).where(User.status != UserStatus.DELETED)

    if status == "pending":
        condition = (
            User.kyc_level == KycLevel.L0,
            User.kyc_real_name.is_not(None),
            User.kyc_id_number.is_not(None),
        )
        query = query.where(*condition)
        count_query = count_query.where(*condition)
    elif status == "verified":
        condition = User.kyc_level.in_((KycLevel.L1, KycLevel.L2))
        query = query.where(condition)
        count_query = count_query.where(condition)
    else:
        condition = or_(
            User.kyc_level.in_((KycLevel.L1, KycLevel.L2)),
            User.kyc_real_name.is_not(None),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(User.updated_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    items = []
    for user in users:
        id_number = None
        id_number_masked = None
        if user.kyc_id_number:
            try:
                plain = decrypt_id_number(user.kyc_id_number)
                id_number = plain
                id_number_masked = mask_id_number(plain)
            except Exception:
                id_number_masked = None
        items.append(
            {
                "user_id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "real_name": user.kyc_real_name,
                "id_number": id_number,
                "id_number_masked": id_number_masked,
                "kyc_level": user.kyc_level,
                "kyc_status": derive_kyc_status(user),
                "submitted_at": user.updated_at.isoformat(),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def admin_review_kyc(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str,
    admin_id: UUID,
    admin_note: str | None = None,
) -> dict:
    if action not in ("approve", "reject"):
        raise_auth_error(code=47004, message="action must be approve or reject", http_status=400)

    user = await db.get(User, user_id)
    if user is None:
        raise_auth_error(code=ERR_KYC_NOT_FOUND, message="user not found", http_status=404)

    if derive_kyc_status(user) != "pending":
        raise_auth_error(code=ERR_KYC_NOT_FOUND, message="no pending kyc submission", http_status=404)

    if action == "approve":
        user.kyc_level = KycLevel.L1
        await log_admin_action(
            db,
            admin_id=admin_id,
            action="approve_kyc",
            target_type="user",
            target_id=str(user_id),
            detail=admin_note or user.kyc_real_name,
        )
    else:
        user.kyc_real_name = None
        user.kyc_id_number = None
        user.kyc_id_number_hash = None
        await log_admin_action(
            db,
            admin_id=admin_id,
            action="reject_kyc",
            target_type="user",
            target_id=str(user_id),
            detail=admin_note,
        )

    await db.commit()
    await db.refresh(user)
    return kyc_status_for_user(user).model_dump()
