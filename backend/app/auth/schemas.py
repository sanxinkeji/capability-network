from typing import Any
from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.auth.constants import KycLevel
from app.auth.security import is_valid_email, is_valid_phone


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    invite_code: str | None = Field(default=None, max_length=64)


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    verification_required: bool = False
    email: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=8)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class KycStatusInfo(BaseModel):
    kyc_level: KycLevel
    kyc_status: str
    kyc_real_name: str | None = None
    kyc_id_number_masked: str | None = None


class KycSubmitRequest(BaseModel):
    real_name: str = Field(min_length=2, max_length=50)
    id_number: str = Field(min_length=15, max_length=18)


class UserProfile(BaseModel):
    id: UUID
    email: str
    phone: str | None
    display_name: str
    avatar_url: str | None
    role: str
    status: str
    kyc_level: KycLevel
    kyc_status: str = "none"
    kyc_real_name: str | None = None
    kyc_id_number_masked: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class CreateApiKeyRequest(BaseModel):
    platform_user_id: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=100)
    rotate_key_id: UUID | None = None


class ApiKeyResponse(BaseModel):
    id: UUID
    api_key: str
    platform_user_id: str
    name: str | None
    key_prefix: str
    status: str
    created_at: str


class ApiKeyInfo(BaseModel):
    id: UUID
    platform_user_id: str
    name: str | None
    key_prefix: str
    status: str
    created_at: str


class CurrentUser(BaseModel):
    id: UUID
    role: str
    caller_type: str
    kyc_level: KycLevel
    platform_user_id: str | None = None
    api_key_id: UUID | None = None


class AuthError(Exception):
    def __init__(
        self,
        *,
        code: int,
        message: str,
        http_status: int = 400,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.errors = errors


def auth_error_response(exc: AuthError) -> JSONResponse:
    body: dict[str, Any] = {
        "code": exc.code,
        "message": exc.message,
        "data": None,
    }
    if exc.errors:
        body["errors"] = exc.errors
    return JSONResponse(status_code=exc.http_status, content=body)


def raise_auth_error(
    *,
    code: int,
    message: str,
    http_status: int = 400,
    errors: list[dict[str, str]] | None = None,
) -> None:
    raise AuthError(code=code, message=message, http_status=http_status, errors=errors)


def validate_account_format(account: str) -> str:
    if is_valid_email(account) or is_valid_phone(account):
        return account
    raise ValueError("invalid account format")
