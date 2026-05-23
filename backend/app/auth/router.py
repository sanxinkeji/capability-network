from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_human, get_current_user
from app.auth.schemas import (
    CreateApiKeyRequest,
    KycSubmitRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
    UserProfile,
)
from app.auth.kyc_service import submit_kyc
from app.auth.service import (
    create_api_key,
    list_api_keys,
    login_user,
    refresh_access_token,
    register_user,
    resend_verification_email,
    revoke_api_key,
    user_to_profile,
    verify_user_email,
)
from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import (
    check_rate_limit,
    enforce_login_rate_limit,
    enforce_register_rate_limit,
    resolve_client_ip,
)
from app.schemas.response import success

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])


async def enforce_api_key_issue_rate_limit(
    current=Depends(get_current_human),
) -> None:
    await check_rate_limit(
        key=f"rl:apikey:user:{current.id}",
        max_requests=settings.RATE_LIMIT_API_KEY_ISSUE_MAX,
        window_seconds=settings.RATE_LIMIT_API_KEY_ISSUE_WINDOW_SECONDS,
    )


@auth_router.post("/register", dependencies=[Depends(enforce_register_rate_limit)])
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await register_user(db, payload)
    return success(tokens.model_dump())


@auth_router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await verify_user_email(db, email=str(payload.email), code=payload.code)
    return success(tokens.model_dump())


@auth_router.post("/resend-verification")
async def resend_verification(
    payload: ResendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await resend_verification_email(db, email=str(payload.email))
    return success({"sent": True})


@auth_router.post("/login", dependencies=[Depends(enforce_login_rate_limit)])
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await login_user(db, payload, client_ip=await resolve_client_ip(request))
    return success(tokens.model_dump())


@auth_router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await refresh_access_token(db, payload.refresh_token)
    return success(tokens.model_dump())


@users_router.post("/kyc/submit")
async def submit_kyc_endpoint(
    payload: KycSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_human),
):
    result = await submit_kyc(
        db,
        user_id=current.id,
        real_name=payload.real_name,
        id_number=payload.id_number,
    )
    return success(result.model_dump())


@users_router.get("/me")
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    from app.auth.service import get_user_by_id

    user = await get_user_by_id(db, current.id)
    if user is None:
        from app.auth.schemas import raise_auth_error

        raise_auth_error(code=40401, message="user not found", http_status=404)
    profile = user_to_profile(user)
    data = profile.model_dump()
    data["caller_type"] = current.caller_type
    if current.platform_user_id:
        data["platform_user_id"] = current.platform_user_id
    return success(data)


@agent_router.post(
    "/api-keys",
    dependencies=[Depends(enforce_api_key_issue_rate_limit)],
)
async def issue_api_key(
    payload: CreateApiKeyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_human),
):
    from app.auth.service import get_user_by_id

    user = await get_user_by_id(db, current.id)
    if user is None:
        from app.auth.schemas import raise_auth_error

        raise_auth_error(code=40401, message="user not found", http_status=404)
    result = await create_api_key(db, user=user, payload=payload)
    return success(result.model_dump())


@agent_router.get("/api-keys")
async def list_api_keys_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_human),
):
    keys = await list_api_keys(db, user_id=current.id)
    return success({"items": [k.model_dump() for k in keys]})


@agent_router.delete("/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_human),
):
    result = await revoke_api_key(db, user_id=current.id, key_id=key_id)
    return success(result.model_dump())
