import pytest

from app.auth.constants import API_KEY_PREFIX, KycLevel
from app.auth.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    is_api_key_format,
    is_valid_email,
    is_valid_phone,
    phone_to_email,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_decode():
    token, expires_in = create_access_token(user_id="00000000-0000-0000-0000-000000000001", role="user")
    assert expires_in == 3600
    from app.auth.security import decode_access_token

    payload = decode_access_token(token)
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["role"] == "user"


def test_api_key_format():
    full_key, key_hash, prefix = generate_api_key()
    assert full_key.startswith(API_KEY_PREFIX)
    assert len(key_hash) == 64
    assert prefix == full_key[:12]
    assert is_api_key_format(full_key)
    assert not is_api_key_format("Bearer jwt-token")


def test_phone_email_helpers():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("bad-email")
    assert is_valid_phone("+8613800138000")
    assert not is_valid_phone("123")
    assert phone_to_email("+8613800138000") == "8613800138000@phone.capability.network"


def test_kyc_levels():
    assert KycLevel.L0 == "L0"
    assert list(KycLevel) == [KycLevel.L0, KycLevel.L1, KycLevel.L2]
