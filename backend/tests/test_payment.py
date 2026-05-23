"""支付限额 enforcement 与 Stripe webhook 验签。"""

import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.deals.tasks import clear_scheduled_tasks
from app.deals.webhooks import clear_registry
from app.main import app as fastapi_app
from app.platform.models import PlatformSettings
from app.wallets.payment_provider import PlatformPaymentConfig, StripeProvider

import app.auth.models  # noqa: F401
import app.deals.models  # noqa: F401
import app.intents.models  # noqa: F401
import app.matching.models  # noqa: F401
import app.offers.models  # noqa: F401
import app.platform.models  # noqa: F401
import app.wallets.models  # noqa: F401

API = "/api/v1"
WEBHOOK_SECRET = "whsec_test_secret_for_pytest"


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
    email = f"pay-test-{suffix}@example.com"
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
        from app.auth.models import User

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


async def _set_payment_limits(
    session_factory,
    *,
    daily_limit_cents: int | None = None,
    max_daily_count: int | None = None,
) -> None:
    async with session_factory() as db:
        result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
        row = result.scalar_one_or_none()
        if row is None:
            row = PlatformSettings(id=1, site_name="Capability")
            db.add(row)
        row.payment_enabled = True
        row.payment_wechat_enabled = True
        row.payment_daily_limit_cents = daily_limit_cents
        row.max_daily_payment_count = max_daily_count
        await db.commit()


def _stripe_checkout_payload(*, provider_ref: str, amount_cents: int) -> bytes:
    return json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": provider_ref,
                    "amount_total": amount_cents,
                }
            },
        }
    ).encode()


@pytest.mark.asyncio
async def test_deposit_daily_amount_limit_exceeded(client):
    ac, session_factory = client
    await _set_payment_limits(session_factory, daily_limit_cents=5000)
    _, user_token = await _register(ac, suffix="daily-limit")

    first = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(user_token),
        json={"amount_cents": 3000, "channel": "wechat"},
    )
    assert first.status_code == 200, first.text

    second = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(user_token),
        json={"amount_cents": 3000, "channel": "wechat"},
    )
    assert second.status_code == 422
    body = second.json()
    assert body["code"] == 46006
    assert "daily payment amount limit" in body["message"]


@pytest.mark.asyncio
async def test_deposit_daily_count_limit_exceeded(client):
    ac, session_factory = client
    await _set_payment_limits(session_factory, max_daily_count=1)
    _, user_token = await _register(ac, suffix="daily-count")

    first = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(user_token),
        json={"amount_cents": 1000, "channel": "wechat"},
    )
    assert first.status_code == 200, first.text

    second = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(user_token),
        json={"amount_cents": 1000, "channel": "wechat"},
    )
    assert second.status_code == 422
    body = second.json()
    assert body["code"] == 46006
    assert "daily payment count limit" in body["message"]


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature_rejected(client):
    ac, _ = client
    provider = StripeProvider(
        config=PlatformPaymentConfig(
            stripe_public_key="pk_test_x",
            stripe_secret_key="sk_test_x",
            stripe_webhook_secret=WEBHOOK_SECRET,
        )
    )
    payload = _stripe_checkout_payload(provider_ref="cn_st_test", amount_cents=1000)

    with patch("app.wallets.service.get_payment_provider", return_value=provider):
        resp = await ac.post(
            f"{API}/wallets/payment-notify/stripe",
            content=payload,
            headers={"stripe-signature": "t=123,v1=invalid"},
        )

    assert resp.status_code == 200
    assert resp.json()["received"] is False


@pytest.mark.asyncio
async def test_stripe_provider_rejects_missing_signature():
    provider = StripeProvider(
        config=PlatformPaymentConfig(
            stripe_public_key="pk_test_x",
            stripe_secret_key="sk_test_x",
            stripe_webhook_secret=WEBHOOK_SECRET,
        )
    )
    payload = _stripe_checkout_payload(provider_ref="cn_st_test", amount_cents=1000)
    result = await provider.verify_notify(payload=payload, headers={})
    assert result is None


@pytest.mark.asyncio
async def test_admin_refund_paid_deposit_order(client):
    ac, session_factory = client
    user_email, user_token = await _register(ac, suffix="refund-user")
    admin_email, _ = await _register(ac, suffix="refund-admin")
    await _promote_to_admin(session_factory, admin_email)
    admin_token = await _login(ac, admin_email)

    deposit = await ac.post(
        f"{API}/wallets/deposit-orders",
        headers=_auth(user_token),
        json={"amount_cents": 5000, "channel": "wechat"},
    )
    assert deposit.status_code == 200, deposit.text
    order_id = deposit.json()["data"]["id"]

    wallet_before = await ac.get(f"{API}/wallets/me", headers=_auth(user_token))
    assert wallet_before.json()["data"]["balance_available"] == 5000

    refund = await ac.patch(
        f"{API}/admin/payment-orders/{order_id}",
        headers=_auth(admin_token),
        json={"action": "refund", "admin_note": "test refund"},
    )
    assert refund.status_code == 200, refund.text
    assert refund.json()["data"]["status"] == "refunded"

    wallet_after = await ac.get(f"{API}/wallets/me", headers=_auth(user_token))
    assert wallet_after.json()["data"]["balance_available"] == 0
    assert user_email  # used
