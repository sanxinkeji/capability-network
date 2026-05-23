import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def freeze(db: AsyncSession, *, user_id: UUID, deal_id: UUID, amount: int):
    from app.wallets import service as wallet_service

    return await wallet_service.freeze(
        db, user_id=user_id, deal_id=deal_id, amount=amount
    )


async def settle(db: AsyncSession, *, deal_id: UUID):
    from app.wallets import service as wallet_service

    return await wallet_service.settle(db, deal_id=deal_id)


async def unfreeze(db: AsyncSession, *, user_id: UUID, deal_id: UUID, amount: int | None = None):
    from app.wallets import service as wallet_service

    return await wallet_service.unfreeze(
        db, user_id=user_id, deal_id=deal_id, amount=amount
    )
