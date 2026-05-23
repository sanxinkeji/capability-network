from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import KycLevel
from app.auth.dependencies import get_current_user, require_kyc
from app.auth.schemas import CurrentUser
from app.core.database import get_db
from app.core.rate_limit import enforce_payment_notify_rate_limit
from app.schemas.response import success
from app.platform.code_schemas import RedeemCodeRequest
from app.platform.enforcement import require_wallet_enabled
from app.platform.service import get_or_create_settings
from app.wallets.schemas import CreateDepositOrderRequest, WithdrawRequestPayload
from app.wallets.service import (
    create_deposit_order,
    create_withdraw_request,
    get_deposit_order,
    get_my_wallet,
    handle_payment_notify,
    list_my_withdrawals,
    list_wallet_ledger,
    redeem_recharge_card,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/me")
async def get_wallet_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    wallet = await get_my_wallet(db, user_id=current.id)
    return success(wallet.model_dump())


@router.get("/ledger")
async def get_wallet_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await list_wallet_ledger(db, user_id=current.id, page=page, page_size=page_size)
    return success(data)


@router.post("/deposit-orders")
async def create_deposit_order_endpoint(
    payload: CreateDepositOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_wallet_enabled(settings)
    result = await create_deposit_order(
        db,
        user_id=current.id,
        amount_cents=payload.amount_cents,
        channel=payload.channel,
    )
    return success(result.model_dump())


@router.get("/deposit-orders/{order_id}")
async def get_deposit_order_endpoint(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    result = await get_deposit_order(db, user_id=current.id, order_id=order_id)
    return success(result.model_dump())


@router.post("/redeem")
async def redeem_code_endpoint(
    payload: RedeemCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    settings = await get_or_create_settings(db)
    require_wallet_enabled(settings)
    wallet = await redeem_recharge_card(db, user_id=current.id, code_str=payload.code)
    return success(wallet.model_dump())


@router.post("/withdraw")
async def withdraw_wallet(
    payload: WithdrawRequestPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_kyc(KycLevel.L1))],
):
    result = await create_withdraw_request(
        db,
        user_id=current.id,
        amount_cents=payload.amount_cents,
        payout_method=payload.payout_method,
        payout_account=payload.payout_account,
        payout_name=payload.payout_name,
    )
    return success(result.model_dump())


@router.get("/withdrawals")
async def list_withdrawals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    data = await list_my_withdrawals(db, user_id=current.id, page=page, page_size=page_size)
    return success(data)


@router.post("/payment-notify/wechat", dependencies=[Depends(enforce_payment_notify_rate_limit)])
async def wechat_payment_notify(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    ok = await handle_payment_notify(db, channel="wechat", payload=payload, headers=headers)
    if ok:
        return {"code": "SUCCESS", "message": "成功"}
    return {"code": "FAIL", "message": "失败"}


@router.post("/payment-notify/alipay", dependencies=[Depends(enforce_payment_notify_rate_limit)])
async def alipay_payment_notify(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    ok = await handle_payment_notify(db, channel="alipay", payload=payload, headers=headers)
    return "success" if ok else "failure"


@router.post("/payment-notify/easypay", dependencies=[Depends(enforce_payment_notify_rate_limit)])
async def easypay_payment_notify(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = await request.body()
    if not payload:
        form = await request.form()
        payload = urlencode({k: str(v) for k, v in form.items()}).encode()
    headers = {k.lower(): v for k, v in request.headers.items()}
    ok = await handle_payment_notify(db, channel="easypay", payload=payload, headers=headers)
    return "success" if ok else "fail"


@router.post("/payment-notify/stripe", dependencies=[Depends(enforce_payment_notify_rate_limit)])
async def stripe_payment_notify(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    ok = await handle_payment_notify(db, channel="stripe", payload=payload, headers=headers)
    return {"received": ok}

