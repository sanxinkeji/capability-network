"""KYC 提交、审核与提现门禁。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.constants import KycLevel
from app.auth.kyc_crypto import is_valid_id_number
from app.auth.models import User
from app.core.database import Base, get_db
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.wallets.models  # noqa: F401

API = "/api/v1"

# 校验位合法的测试身份证号
TEST_ID_NUMBER = "110101199001011237"
assert is_valid_id_number(TEST_ID_NUMBER)


@pytest.fixture
async def client():
    clear_registry()
    clear_scheduled_tasks()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_factory
    fastapi_app.dependency_overrides.clear()
    clear_scheduled_tasks()
    await engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client: AsyncClient, *, suffix: str) -> tuple[str, str]:
    email = f"kyc-test-{suffix}@example.com"
    resp = await client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": f"User {suffix}",
        },
    )
    assert resp.status_code == 200, resp.text
    return email, resp.json()["data"]["access_token"]


async def _promote_to_admin(session_factory, email: str) -> None:
    async with session_factory() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = "admin"
        await db.commit()


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        f"{API}/auth/login",
        json={"account": email, "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def _fund_wallet(client: AsyncClient, token: str, amount_cents: int = 200_000) -> None:
    resp = await client.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(token),
        json={"amount_cents": amount_cents, "channel": "wechat"},
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_kyc_submit_and_admin_review(client):
    ac, session_factory = client
    user_email, user_token = await _register(ac, suffix="user")
    admin_email, _ = await _register(ac, suffix="admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    submit_resp = await ac.post(
        f"{API}/users/kyc/submit",
        headers=_auth(user_token),
        json={"real_name": "张三", "id_number": TEST_ID_NUMBER},
    )
    assert submit_resp.status_code == 200, submit_resp.text
    submit_data = submit_resp.json()["data"]
    assert submit_data["kyc_status"] == "pending"
    assert submit_data["kyc_real_name"] == "张三"
    assert submit_data["kyc_id_number_masked"].startswith("110")
    assert submit_data["kyc_id_number_masked"].endswith("1237")

    me_resp = await ac.get(f"{API}/users/me", headers=_auth(user_token))
    assert me_resp.json()["data"]["kyc_status"] == "pending"

    list_resp = await ac.get(f"{API}/admin/kyc?status=pending", headers=_auth(admin_token))
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["real_name"] == "张三"
    assert items[0]["id_number"] == TEST_ID_NUMBER

    async with session_factory() as db:
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one()
        user_id = user.id

    approve_resp = await ac.patch(
        f"{API}/admin/kyc/{user_id}",
        headers=_auth(admin_token),
        json={"action": "approve"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["data"]["kyc_level"] == KycLevel.L1
    assert approve_resp.json()["data"]["kyc_status"] == "verified"


@pytest.mark.asyncio
async def test_withdraw_requires_kyc_l1(client):
    ac, session_factory = client
    user_email, user_token = await _register(ac, suffix="withdraw")
    admin_email, _ = await _register(ac, suffix="withdraw-admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)
    await _fund_wallet(ac, user_token)

    withdraw_payload = {
        "amount_cents": 10000,
        "payout_method": "alipay",
        "payout_account": "test@alipay.com",
        "payout_name": "张三",
    }

    blocked = await ac.post(f"{API}/wallets/withdraw", headers=_auth(user_token), json=withdraw_payload)
    assert blocked.status_code == 403
    assert blocked.json()["code"] == 41006

    submit_resp = await ac.post(
        f"{API}/users/kyc/submit",
        headers=_auth(user_token),
        json={"real_name": "张三", "id_number": TEST_ID_NUMBER},
    )
    assert submit_resp.status_code == 200

    still_blocked = await ac.post(f"{API}/wallets/withdraw", headers=_auth(user_token), json=withdraw_payload)
    assert still_blocked.status_code == 403

    async with session_factory() as db:
        result = await db.execute(select(User).where(User.email == user_email))
        user_id = result.scalar_one().id

    await ac.patch(
        f"{API}/admin/kyc/{user_id}",
        headers=_auth(admin_token),
        json={"action": "approve"},
    )

    allowed = await ac.post(f"{API}/wallets/withdraw", headers=_auth(user_token), json=withdraw_payload)
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_kyc_invalid_id_rejected(client):
    ac, _ = client
    _, user_token = await _register(ac, suffix="invalid-id")

    resp = await ac.post(
        f"{API}/users/kyc/submit",
        headers=_auth(user_token),
        json={"real_name": "李四", "id_number": "123456789012345678"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == 41014


@pytest.mark.asyncio
async def test_kyc_crypto_helpers():
    from app.auth.kyc_crypto import decrypt_id_number, encrypt_id_number, hash_id_number, mask_id_number

    encrypted = encrypt_id_number(TEST_ID_NUMBER)
    assert encrypted != TEST_ID_NUMBER
    assert decrypt_id_number(encrypted) == TEST_ID_NUMBER
    assert hash_id_number(TEST_ID_NUMBER) == hash_id_number(TEST_ID_NUMBER.lower())
    assert mask_id_number(TEST_ID_NUMBER) == "110***********1237"
