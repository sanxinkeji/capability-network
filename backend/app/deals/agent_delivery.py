"""Agent 通道辅助判断。"""

from __future__ import annotations

from app.offers.models import Offer
from app.offers.schemas import parse_tags_payload

AGENT_AUTO_DELIVER_SOURCE = "agent_deliver"


def is_agent_auto_delivered(delivery_text: str | None) -> bool:
    if not delivery_text:
        return False
    return AGENT_AUTO_DELIVER_SOURCE in delivery_text or "agent" in delivery_text.lower()


def offer_channel_is_agent(offer: Offer) -> bool:
    meta = parse_tags_payload(offer.tags)
    return str(meta.get("channel", "human")) == "agent"
