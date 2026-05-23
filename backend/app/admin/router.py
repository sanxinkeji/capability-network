from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.admin.dependencies import require_admin
from app.admin.schemas import (
    AdminIntentStatusUpdate,
    AdminKycAction,
    AdminOfferStatusUpdate,
    AdminPaymentOrderAction,
    AdminUserCredit,
    AdminUserStatusUpdate,
    AdminWithdrawAction,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.admin.service import (
    admin_revoke_api_key,
    admin_update_intent_status,
    admin_update_offer_status,
    create_announcement,
    delete_announcement,
    get_agent_stats,
    get_dashboard_analytics,
    get_deal_admin,
    get_ops_health,
    get_payment_stats,
    get_platform_stats,
    list_admin_api_keys,
    list_all_deals,
    list_all_intents,
    list_all_offers,
    list_announcements,
    list_users,
    update_announcement,
    update_user_status,
)
from app.auth.constants import UserStatus
from app.auth.kyc_service import admin_review_kyc, list_kyc_submissions
from app.auth.schemas import CurrentUser
from app.core.config import settings as app_settings
from app.core.database import get_db
from app.platform.code_schemas import GeneratePlatformCodesRequest
from app.core.config import settings as app_settings
from app.platform.backups import list_database_backups, trigger_database_backup
from app.platform.codes import generate_platform_codes, list_platform_codes
from app.platform.schemas import PlatformSettingsUpdate
from app.platform.service import (
    get_payment_config_info,
    get_platform_settings,
    list_audit_logs,
    update_platform_settings,
)
from app.schemas.response import success
from app.wallets.service import (
    admin_credit_user_wallet,
    admin_process_withdraw,
    admin_refund_deposit_order,
    list_admin_deposit_orders,
    list_admin_ledger,
    list_admin_withdrawals,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    stats = await get_platform_stats(db)
    return success(stats.model_dump())


@router.get("/payment-stats")
async def admin_payment_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    days: Annotated[int, Query(ge=1, le=90)] = 7,
):
    stats = await get_payment_stats(db, days=days)
    return success(stats.model_dump())


@router.get("/dashboard")
async def admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    days: Annotated[int, Query(ge=1, le=90)] = 7,
):
    data = await get_dashboard_analytics(db, days=days)
    return success(data.model_dump())


@router.get("/ops-health")
async def admin_ops_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await get_ops_health(db)
    return success(data.model_dump())


@router.get("/users")
async def admin_list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    data = await list_users(db, page=page, page_size=page_size, status=status, search=search)
    return success(data)


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: UUID,
    payload: AdminUserStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    if payload.status not in (UserStatus.ACTIVE, UserStatus.SUSPENDED):
        from app.auth.schemas import raise_auth_error

        raise_auth_error(code=40001, message="status must be active or suspended", http_status=400)
    profile = await update_user_status(
        db, user_id=user_id, status=payload.status, current=current
    )
    return success(profile.model_dump())


@router.get("/deals")
async def admin_list_deals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
):
    data = await list_all_deals(db, page=page, page_size=page_size, status=status)
    return success(data)


@router.get("/deals/{deal_id}")
async def admin_get_deal(
    deal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    deal = await get_deal_admin(db, deal_id=deal_id, current=current)
    return success(deal.model_dump())


@router.get("/offers")
async def admin_list_offers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
):
    data = await list_all_offers(db, page=page, page_size=page_size, status=status)
    return success(data)


@router.get("/intents")
async def admin_list_intents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
):
    data = await list_all_intents(db, page=page, page_size=page_size, status=status)
    return success(data)


@router.get("/withdrawals")
async def admin_list_withdrawals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
):
    data = await list_admin_withdrawals(db, page=page, page_size=page_size, status=status)
    return success(data)


@router.patch("/offers/{offer_id}/status")
async def admin_update_offer(
    offer_id: UUID,
    payload: AdminOfferStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_update_offer_status(
        db, offer_id=offer_id, status=payload.status, admin_id=current.id
    )
    return success(data)


@router.patch("/intents/{intent_id}/status")
async def admin_update_intent(
    intent_id: UUID,
    payload: AdminIntentStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_update_intent_status(
        db, intent_id=intent_id, status=payload.status, admin_id=current.id
    )
    return success(data)


@router.get("/settings")
async def admin_get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    settings = await get_platform_settings(db)
    payment = await get_payment_config_info(db)
    return success({"settings": settings.model_dump(), "payment": payment.model_dump()})


@router.patch("/settings")
async def admin_update_settings(
    payload: PlatformSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    settings = await update_platform_settings(db, payload=payload, admin_id=current.id)
    payment = await get_payment_config_info(db)
    return success({"settings": settings.model_dump(), "payment": payment.model_dump()})


@router.get("/payment-orders")
async def admin_list_payment_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    data = await list_admin_deposit_orders(
        db,
        page=page,
        page_size=page_size,
        status=status,
        channel=channel,
        search=search,
    )
    return success(data)


@router.patch("/payment-orders/{order_id}")
async def admin_refund_payment_order(
    order_id: UUID,
    payload: AdminPaymentOrderAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    if payload.action.lower() != "refund":
        from app.auth.schemas import raise_auth_error

        raise_auth_error(code=46010, message="invalid action", http_status=400)
    data = await admin_refund_deposit_order(
        db,
        order_id=order_id,
        admin_id=current.id,
        admin_note=payload.admin_note,
    )
    return success(data)


@router.post("/users/{user_id}/credit")
async def admin_credit_user(
    user_id: UUID,
    payload: AdminUserCredit,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_credit_user_wallet(
        db,
        user_id=user_id,
        amount_cents=payload.amount_cents,
        admin_id=current.id,
        note=payload.note,
    )
    return success(data)


@router.get("/announcements")
async def admin_list_announcements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    data = await list_announcements(
        db, page=page, page_size=page_size, status=status, search=search
    )
    return success(data)


@router.post("/announcements")
async def admin_create_announcement(
    payload: AnnouncementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await create_announcement(
        db, admin_id=current.id, payload=payload.model_dump(exclude_unset=True)
    )
    return success(data)


@router.patch("/announcements/{announcement_id}")
async def admin_update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await update_announcement(
        db,
        announcement_id=announcement_id,
        admin_id=current.id,
        payload=payload.model_dump(exclude_unset=True),
    )
    return success(data)


@router.delete("/announcements/{announcement_id}")
async def admin_delete_announcement(
    announcement_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    await delete_announcement(db, announcement_id=announcement_id, admin_id=current.id)
    return success(None)


@router.get("/ledger")
async def admin_list_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    entry_type: Annotated[str | None, Query()] = None,
):
    data = await list_admin_ledger(db, page=page, page_size=page_size, entry_type=entry_type)
    return success(data)


@router.get("/backups")
async def admin_list_backups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
):
    data = await list_database_backups(db, page=page, page_size=page_size)
    return success(data)


@router.post("/backups/trigger")
async def admin_trigger_backup(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    dry_run: Annotated[bool, Query()] = False,
):
    effective_dry_run = dry_run or app_settings.BACKUP_DRY_RUN
    data = await trigger_database_backup(
        db,
        admin_id=current.id,
        dry_run=effective_dry_run,
    )
    return success(data)


@router.get("/audit-logs")
async def admin_list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
):
    data = await list_audit_logs(db, page=page, page_size=page_size)
    return success(data)


@router.get("/kyc")
async def admin_list_kyc(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
):
    data = await list_kyc_submissions(db, page=page, page_size=page_size, status=status)
    return success(data)


@router.patch("/kyc/{user_id}")
async def admin_update_kyc(
    user_id: UUID,
    payload: AdminKycAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_review_kyc(
        db,
        user_id=user_id,
        action=payload.action,
        admin_id=current.id,
        admin_note=payload.admin_note,
    )
    return success(data)


@router.patch("/withdrawals/{withdraw_id}")
async def admin_update_withdraw(
    withdraw_id: UUID,
    payload: AdminWithdrawAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_process_withdraw(
        db,
        withdraw_id=withdraw_id,
        action=payload.action,
        admin_note=payload.admin_note,
        provider_ref=payload.provider_ref,
        admin_id=current.id,
    )
    return success(data)


@router.get("/codes")
async def admin_list_codes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    code_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    batch_id: Annotated[UUID | None, Query()] = None,
):
    data = await list_platform_codes(
        db,
        page=page,
        page_size=page_size,
        code_type=code_type,
        status=status,
        batch_id=batch_id,
    )
    return success(data)


@router.post("/codes/generate")
async def admin_generate_codes(
    payload: GeneratePlatformCodesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await generate_platform_codes(
        db,
        admin_id=current.id,
        code_type=payload.code_type,
        count=payload.count,
        expires_at=payload.expires_at,
        value_cents=payload.value_cents,
    )
    return success(data)


@router.get("/agent-stats")
async def admin_agent_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    stats = await get_agent_stats(db)
    return success(stats.model_dump())


@router.get("/agent-keys")
async def admin_list_agent_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
):
    data = await list_admin_api_keys(
        db, page=page, page_size=page_size, status=status, search=search
    )
    return success(data)


@router.delete("/agent-keys/{key_id}")
async def admin_revoke_agent_key(
    key_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_admin)],
):
    data = await admin_revoke_api_key(db, key_id=key_id, admin_id=current.id)
    return success(data)
