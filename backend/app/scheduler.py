"""Optional in-process daily reparse scheduler (TZ 3.1 cron, TZ 4 freshness)."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .config import settings
from .db import SessionLocal
from .parsers.pipeline import mark_stale_inactive, purge_old_raw, run_full
from .parsers.registry import LOCAL_SOURCES

logger = logging.getLogger("medservice.scheduler")
scheduler = BackgroundScheduler(timezone="UTC")


def _daily_job() -> None:
    db = SessionLocal()
    try:
        result = run_full(db, list(LOCAL_SOURCES))
        stale = mark_stale_inactive(db)
        purged = purge_old_raw(db)
        logger.info(
            "daily reparse done: runs=%s stale_marked=%s raw_purged=%s",
            [(r["source"], r["status"]) for r in result.get("runs", [])],
            stale,
            purged,
        )
    except Exception:  # never crash the scheduler thread
        logger.exception("daily reparse failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.enable_scheduler:
        return
    scheduler.add_job(
        _daily_job,
        "cron",
        hour=settings.scheduler_cron_hour,
        id="daily_reparse",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler started (daily at %02d:00 UTC)", settings.scheduler_cron_hour)


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
