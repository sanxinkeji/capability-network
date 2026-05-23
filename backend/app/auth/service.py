from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import (
    ERR_ACCOUNT_SUSPENDED,
    ERR_API_KEY_INVALID,
    ERR_INVALID_CREDENTIALS,
    ERR_REFRESH_TOKEN_EXPIRED,
    ERR_REFRESH_TOKEN_INVALID,
    ApiKeyStatus,
    KycLevel,
    UserStatus,
)
from app.auth.email_verification import (
    assert_email_verified_for_login,
    issue_email_verification,
    verify_email_code,
)
from app.auth.models import ApiKey, RefreshToken, User
from app.auth.schemas import (
    ApiKeyInfo,
    ApiKeyResponse,
    CreateApiKeyRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserProfile,
    raise_auth_error,
)
from app.auth.security import (
    create_access_token,
    generate_api_key,
    generate_refresh_token,
    hash_password,
    hash_token,
    is_valid_email,
    is_valid_phone,
    phone_to_email,
    refresh_token_expires_at,
    verify_password,
)
from app.core.rate_limit import (
    check_login_not_locked,
    clear_login_attempts,
    record_login_failure,
)
from app.platform.codes import assert_registration_allowed, consume_invite_code
from app.platform.email_policy import assert_email_domain_allowed
from app.platform.enforcement import require_agent_enabled
from app.platform.service import get_or_create_settings
from app.wallets.service import _append_ledger, get_or_create_wallet
from app.wallets.constants import LedgerEntryType


def _default_display_name(email: str) -> str:
    local = email.split("@", 1)[0].strip()
    return local or "用户"


async def register_user(db: AsyncSession, payload: RegisterRequest) -> RegisterResponse:
    settings = await get_or_create_settings(db)
    invite_record = await assert_registration_allowed(db, settings, invite_code=payload.invite_code)

    email = str(payload.email).lower()
    assert_email_domain_allowed(email, settings.registration_email_domains)

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise_auth_error(
            code=40902,
            message="email already registered",
            http_status=409,
        )

    user = User(
        email=email,
        phone=None,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or _default_display_name(email),
        kyc_level=KycLevel.L0,
    )
    if settings.email_verification_required:
        user.email_verified_at = None
    else:
        user.email_verified_at = datetime.now(UTC)

    db.add(user)
    await db.flush()

    if invite_record is not None:
        await consume_invite_code(db, invite_record, user.id)

    if settings.default_wallet_balance_cents > 0:
        wallet = await get_or_create_wallet(db, user.id)
        wallet.balance_available += settings.default_wallet_balance_cents
        await _append_ledger(
            db,
            wallet_id=wallet.id,
            deal_id=None,
            entry_type=LedgerEntryType.DEPOSIT,
            amount_cents=settings.default_wallet_balance_cents,
            balance_after=wallet.balance_available,
            description="registration bonus",
        )

    if settings.email_verification_required:
        await issue_email_verification(db, user=user, settings=settings)
        await db.commit()
        return RegisterResponse(verification_required=True, email=user.email)

    tokens = await _issue_tokens(db, user)
    return RegisterResponse(
        verification_required=False,
        email=user.email,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


def _ensure_active(user: User) -> None:
    if user.status != UserStatus.ACTIVE:
        raise_auth_error(
            code=ERR_ACCOUNT_SUSPENDED,
            message="account is suspended or deleted",
            http_status=403,
        )


async def _get_user_by_account(db: AsyncSession, account: str) -> User | None:
    account = account.strip()
    if is_valid_email(account):
        result = await db.execute(select(User).where(User.email == account.lower()))
        return result.scalar_one_or_none()
    if is_valid_phone(account):
        result = await db.execute(
            select(User).where(or_(User.phone == account, User.email == phone_to_email(account)))
        )
        return result.scalar_one_or_none()
    return None


async def login_user(
    db: AsyncSession,
    payload: LoginRequest,
    *,
    client_ip: str | None = None,
) -> TokenResponse:
    account = payload.account.strip()
    await check_login_not_locked(account, client_ip)
    user = await _get_user_by_account(db, account)
    if user is None or not verify_password(payload.password, user.password_hash):
        await record_login_failure(account, client_ip)
        raise_auth_error(
            code=ERR_INVALID_CREDENTIALS,
            message="invalid account or password",
            http_status=401,
        )
    await clear_login_attempts(account, client_ip)
    _ensure_active(user)
    settings = await get_or_create_settings(db)
    assert_email_verified_for_login(user, settings)
    return await _issue_tokens(db, user)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    matched = result.scalar_one_or_none()

    if matched is None:
        raise_auth_error(
            code=ERR_REFRESH_TOKEN_INVALID,
            message="invalid refresh token",
            http_status=401,
        )

    if matched.expires_at <= datetime.now(UTC):
        raise_auth_error(
            code=ERR_REFRESH_TOKEN_EXPIRED,
            message="refresh token expired",
            http_status=401,
        )

    user_result = await db.execute(select(User).where(User.id == matched.user_id))
    user = user_result.scalar_one()
    _ensure_active(user)

    matched.revoked_at = datetime.now(UTC)
    return await _issue_tokens(db, user)


async def verify_user_email(
    db: AsyncSession,
    *,
    email: str,
    code: str,
) -> TokenResponse:
    user = await verify_email_code(db, email=email, code=code)
    return await _issue_tokens(db, user)


async def resend_verification_email(db: AsyncSession, *, email: str) -> None:
    settings = await get_or_create_settings(db)
    if not settings.email_verification_required:
        return

    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None or user.email_verified_at is not None:
        return

    await issue_email_verification(db, user=user, settings=settings)
    await db.commit()


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access_token, expires_in = create_access_token(user_id=str(user.id), role=user.role)
    refresh_plain = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_plain),
            expires_at=refresh_token_expires_at(),
        )
    )
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_plain,
        expires_in=expires_in,
    )


def user_to_profile(user: User) -> UserProfile:
    from app.auth.kyc_service import kyc_status_for_user

    kyc = kyc_status_for_user(user)
    return UserProfile(
        id=user.id,
        email=user.email,
        phone=user.phone,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        kyc_level=kyc.kyc_level,
        kyc_status=kyc.kyc_status,
        kyc_real_name=kyc.kyc_real_name,
        kyc_id_number_masked=kyc.kyc_id_number_masked,
        created_at=user.created_at.isoformat(),
    )


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_api_key(
    db: AsyncSession,
    *,
    user: User,
    payload: CreateApiKeyRequest,
) -> ApiKeyResponse:
    from app.platform.service import get_or_create_settings

    settings = await get_or_create_settings(db)
    require_agent_enabled(settings)

    active_count = (
        await db.execute(
            select(func.count()).select_from(ApiKey).where(
                ApiKey.user_id == user.id,
                ApiKey.status == ApiKeyStatus.ACTIVE,
            )
        )
    ).scalar_one()
    if active_count >= settings.agent_max_keys_per_user and not payload.rotate_key_id:
        raise_auth_error(
            code=41008,
            message=f"max {settings.agent_max_keys_per_user} active keys per user",
            http_status=422,
        )

    platform_user_id = payload.platform_user_id.strip()
    if settings.agent_platform_user_id_prefix:
        prefix = settings.agent_platform_user_id_prefix.strip()
        if prefix and not platform_user_id.startswith(prefix):
            platform_user_id = f"{prefix}{platform_user_id}"

    if payload.rotate_key_id:
        old_result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == payload.rotate_key_id,
                ApiKey.user_id == user.id,
                ApiKey.status == ApiKeyStatus.ACTIVE,
            )
        )
        old_key = old_result.scalar_one_or_none()
        if old_key is None:
            raise_auth_error(code=40401, message="api key not found", http_status=404)
        old_key.status = ApiKeyStatus.ROTATED
        old_key.rotated_at = datetime.now(UTC)

    full_key, key_hash, key_prefix = generate_api_key()
    api_key = ApiKey(
        user_id=user.id,
        platform_user_id=platform_user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=payload.name,
        status=ApiKeyStatus.ACTIVE,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        api_key=full_key,
        platform_user_id=api_key.platform_user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        status=api_key.status,
        created_at=api_key.created_at.isoformat(),
    )


async def list_api_keys(db: AsyncSession, *, user_id: UUID) -> list[ApiKeyInfo]:
    settings = await get_or_create_settings(db)
    require_agent_enabled(settings)

    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyInfo(
            id=key.id,
            platform_user_id=key.platform_user_id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            created_at=key.created_at.isoformat(),
        )
        for key in keys
    ]


async def revoke_api_key(
    db: AsyncSession,
    *,
    user_id: UUID,
    key_id: UUID,
) -> ApiKeyInfo:
    settings = await get_or_create_settings(db)
    require_agent_enabled(settings)

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == user_id,
            ApiKey.status == ApiKeyStatus.ACTIVE,
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise_auth_error(code=40401, message="api key not found", http_status=404)

    api_key.status = ApiKeyStatus.REVOKED
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyInfo(
        id=api_key.id,
        platform_user_id=api_key.platform_user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        status=api_key.status,
        created_at=api_key.created_at.isoformat(),
    )


async def authenticate_api_key(db: AsyncSession, raw_key: str) -> tuple[User, ApiKey]:
    settings = await get_or_create_settings(db)
    require_agent_enabled(settings)

    key_hash = hash_token(raw_key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.status == ApiKeyStatus.ACTIVE,
        )
    )
    matched = result.scalar_one_or_none()

    if matched is None:
        raise_auth_error(
            code=ERR_API_KEY_INVALID,
            message="invalid api key",
            http_status=401,
        )

    if matched.expires_at and matched.expires_at <= datetime.now(UTC):
        raise_auth_error(
            code=ERR_API_KEY_INVALID,
            message="api key expired",
            http_status=401,
        )

    user_result = await db.execute(select(User).where(User.id == matched.user_id))
    user = user_result.scalar_one()
    _ensure_active(user)
    return user, matched
