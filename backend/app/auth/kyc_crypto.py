import base64
import hashlib
import re

from cryptography.fernet import Fernet

from app.core.config import settings

ID_NUMBER_PATTERN = re.compile(r"^\d{17}[\dXx]$")
REAL_NAME_PATTERN = re.compile(r"^[\u4e00-\u9fff·A-Za-z\s]{2,50}$")
ID_CHECKSUM_WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
ID_CHECKSUM_CHARS = "10X98765432"


def _fernet_key() -> bytes:
    digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def normalize_id_number(value: str) -> str:
    return value.strip().upper()


def is_valid_real_name(value: str) -> bool:
    name = value.strip()
    return bool(REAL_NAME_PATTERN.match(name))


def is_valid_id_number(value: str) -> bool:
    normalized = normalize_id_number(value)
    if not ID_NUMBER_PATTERN.match(normalized):
        return False
    total = sum(int(normalized[i]) * ID_CHECKSUM_WEIGHTS[i] for i in range(17))
    return ID_CHECKSUM_CHARS[total % 11] == normalized[17]


def hash_id_number(value: str) -> str:
    normalized = normalize_id_number(value)
    return hashlib.sha256(normalized.encode()).hexdigest()


def encrypt_id_number(value: str) -> str:
    normalized = normalize_id_number(value)
    token = Fernet(_fernet_key()).encrypt(normalized.encode())
    return token.decode()


def decrypt_id_number(value: str) -> str:
    token = Fernet(_fernet_key()).decrypt(value.encode())
    return token.decode().upper()


def mask_id_number(value: str) -> str:
    normalized = normalize_id_number(value)
    if len(normalized) < 8:
        return "***"
    return f"{normalized[:3]}***********{normalized[-4:]}"
