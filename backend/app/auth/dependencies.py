from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import (
    CallerType,
    KycLevel,
)
from app.auth.models import User
from app.auth.schemas import CurrentUser, raise_auth_error
from app.auth.security import decode_access_token, is_api_key_format
from app.auth.service import authenticate_api_key, get_user_by_id
from app.core.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


async def resolve_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    token = _extract_bearer_token(credentials)
    if not token:
        raise_auth_error(code=40101, message="missing or invalid authorization", http_status=401)

    if is_api_key_format(token):
        user, api_key = await authenticate_api_key(db, token)
        current = CurrentUser(
            id=user.id,
            role=user.role,
            caller_type=CallerType.AGENT,
            kyc_level=KycLevel(user.kyc_level),
            platform_user_id=api_key.platform_user_id,
            api_key_id=api_key.id,
        )
    else:
        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            raise_auth_error(code=40102, message="token expired", http_status=401)
        except jwt.PyJWTError:
            raise_auth_error(code=40101, message="invalid token", http_status=401)

        user_id = payload.get("sub")
        if not user_id:
            raise_auth_error(code=40101, message="invalid token payload", http_status=401)

        user = await get_user_by_id(db, UUID(user_id))
        if user is None or user.status != "active":
            raise_auth_error(code=40101, message="user not found or inactive", http_status=401)

        current = CurrentUser(
            id=user.id,
            role=payload.get("role", user.role),
            caller_type=CallerType.HUMAN,
            kyc_level=KycLevel(user.kyc_level),
        )

    request.state.current_user = current
    request.state.caller_type = current.caller_type
    return current


async def get_current_user(
    current: Annotated[CurrentUser, Depends(resolve_current_user)],
) -> CurrentUser:
    return current


async def get_current_human(
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current.caller_type != CallerType.HUMAN:
        raise_auth_error(code=40301, message="human authentication required", http_status=403)
    return current


def require_kyc(min_level: KycLevel):
    level_order = {KycLevel.L0: 0, KycLevel.L1: 1, KycLevel.L2: 2}

    async def _checker(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if level_order[current.kyc_level] < level_order[min_level]:
            from app.auth.constants import ERR_KYC_INSUFFICIENT

            raise_auth_error(
                code=ERR_KYC_INSUFFICIENT,
                message=f"kyc level {min_level} or above required",
                http_status=403,
            )
        return current

    return _checker
