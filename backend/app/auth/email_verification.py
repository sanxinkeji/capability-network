import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import (
    ERR_EMAIL_NOT_VERIFIED,
    ERR_EMAIL_VERIFICATION_EXPIRED,
    ERR_EMAIL_VERIFICATION_INVALID,
)
from app.auth.models import User
from app.auth.schemas import raise_auth_error
from app.platform.email_service import send_verification_email
from app.platform.models import PlatformSettings


VERIFICATION_TTL_MINUTES = 15


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def is_email_verified(user: User) -> bool:
    return user.email_verified_at is not None


def assert_email_verified_for_login(user: User, settings: PlatformSettings) -> None:
    if not settings.email_verification_required:
        return
    if user.role == "admin":
        return
    if not is_email_verified(user):
        raise_auth_error(
            code=ERR_EMAIL_NOT_VERIFIED,
            message="email verification required before login",
            http_status=403,
        )


async def issue_email_verification(
    db: AsyncSession,
    *,
    user: User,
    settings: PlatformSettings,
) -> str:
    code = generate_verification_code()
    user.email_verification_code = code
    user.email_verification_expires_at = datetime.now(UTC) + timedelta(minutes=VERIFICATION_TTL_MINUTES)
    user.email_verified_at = None
    await db.flush()
    send_verification_email(
        settings,
        to_email=user.email,
        display_name=user.display_name,
        code=code,
    )
    return code


async def verify_email_code(
    db: AsyncSession,
    *,
    email: str,
    code: str,
) -> User:
    from sqlalchemy import select

    normalized_email = email.strip().lower()
    normalized_code = code.strip()
    if not normalized_code:
        raise_auth_error(
            code=ERR_EMAIL_VERIFICATION_INVALID,
            message="verification code is required",
            http_status=422,
        )

    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None or user.email_verification_code != normalized_code:
        raise_auth_error(
            code=ERR_EMAIL_VERIFICATION_INVALID,
            message="invalid verification code",
            http_status=403,
        )

    expires_at = user.email_verification_expires_at
    if expires_at is None or _as_utc(expires_at) <= datetime.now(UTC):
        raise_auth_error(
            code=ERR_EMAIL_VERIFICATION_EXPIRED,
            message="verification code expired",
            http_status=403,
        )

    user.email_verified_at = datetime.now(UTC)
    user.email_verification_code = None
    user.email_verification_expires_at = None
    await db.flush()
    return user
