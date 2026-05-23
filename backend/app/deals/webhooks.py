import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


@dataclass
class WebhookRegistration:
    id: uuid.UUID
    user_id: uuid.UUID
    url: str
    events: list[str]
    secret: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_registry: dict[uuid.UUID, WebhookRegistration] = {}


def register_webhook(
    *,
    user_id: uuid.UUID,
    url: str,
    events: list[str],
    secret: str | None = None,
) -> WebhookRegistration:
    registration = WebhookRegistration(
        id=uuid.uuid4(),
        user_id=user_id,
        url=url,
        events=events,
        secret=secret,
    )
    _registry[registration.id] = registration
    return registration


def list_webhooks(*, user_id: uuid.UUID) -> list[WebhookRegistration]:
    return [item for item in _registry.values() if item.user_id == user_id]


def get_webhook(webhook_id: uuid.UUID) -> WebhookRegistration | None:
    return _registry.get(webhook_id)


def clear_registry() -> None:
    """测试用：清空内存注册表。"""
    _registry.clear()


def _sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def dispatch_event(*, event: str, payload: dict) -> None:
    message = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    body = json.dumps(message, ensure_ascii=False).encode()

    for registration in _registry.values():
        if event not in registration.events:
            continue
        headers = {"Content-Type": "application/json"}
        if registration.secret:
            headers["X-Webhook-Signature"] = _sign_payload(registration.secret, body)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(registration.url, content=body, headers=headers)
                logger.info(
                    "webhook dispatched event=%s url=%s status=%s",
                    event,
                    registration.url,
                    response.status_code,
                )
        except Exception:
            logger.warning(
                "webhook dispatch failed event=%s url=%s",
                event,
                registration.url,
                exc_info=True,
            )
