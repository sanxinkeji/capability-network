import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.auth.constants import API_KEY_PREFIX, PHONE_EMAIL_DOMAIN
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{6,14}$")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(*, user_id: str, role: str) -> tuple[str, int]:
    expires_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, key_hash, key_prefix)."""
    raw = secrets.token_urlsafe(32)
    full_key = f"{API_KEY_PREFIX}{raw}"
    key_hash = hash_token(full_key)
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


def is_api_key_format(token: str) -> bool:
    return token.startswith(API_KEY_PREFIX)


def phone_to_email(phone: str) -> str:
    normalized = phone.lstrip("+")
    return f"{normalized}@{PHONE_EMAIL_DOMAIN}"


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.match(value))


def is_valid_phone(value: str) -> bool:
    return bool(PHONE_PATTERN.match(value))


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
