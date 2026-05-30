import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from app.deals.constants import AUTO_CONFIRM_DELAY_HOURS

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _job_id(deal_id: UUID) -> str:
    return f"auto_confirm_{deal_id}"


def _ensure_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.start()
        logger.info("APScheduler started for deal auto_confirm jobs")
    return _scheduler


def schedule_auto_confirm(deal_id: UUID, *, delay_hours: int = AUTO_CONFIRM_DELAY_HOURS) -> datetime:
    deadline = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
    scheduler = _ensure_scheduler()
    scheduler.add_job(
        run_auto_confirm_job,
        trigger="date",
        run_date=deadline,
        id=_job_id(deal_id),
        replace_existing=True,
        args=[deal_id],
        misfire_grace_time=3600,
    )
    logger.info(
        "auto_confirm scheduled: deal_id=%s deadline=%s delay_hours=%s",
        deal_id,
        deadline.isoformat(),
        delay_hours,
    )
    return deadline


def cancel_auto_confirm(deal_id: UUID) -> None:
    if _scheduler is None:
        return
    try:
        _scheduler.remove_job(_job_id(deal_id))
        logger.info("auto_confirm cancelled: deal_id=%s", deal_id)
    except JobLookupError:
        pass


def get_scheduled_deadline(deal_id: UUID) -> datetime | None:
    if _scheduler is None:
        return None
    job = _scheduler.get_job(_job_id(deal_id))
    if job is None:
        return None
    return job.next_run_time


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            # 调度器可能绑定在已关闭的事件循环上（测试/重启场景），
            # 关闭失败不应向上抛出；置空后下次会在当前循环重建。
            logger.warning("scheduler shutdown failed", exc_info=True)
        _scheduler = None


def clear_scheduled_tasks() -> None:
    """测试用：关闭调度器并清空任务。"""
    shutdown_scheduler()


async def run_auto_confirm_job(deal_id: UUID) -> None:
    from app.core.database import async_session
    from app.deals.service import auto_confirm_deal

    logger.info("auto_confirm job running: deal_id=%s", deal_id)
    async with async_session() as db:
        await auto_confirm_deal(db, deal_id=deal_id)
