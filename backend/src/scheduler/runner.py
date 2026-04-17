"""APScheduler runner that wires the Phase 3+ jobs into a real background process.

Design:
- `start(app)` is called from the FastAPI lifespan. If APScheduler is not
  installed or `SCHEDULER_ENABLED=false`, it no-ops so tests + minimal
  deployments aren't forced to install the dependency.
- Every job is a thin wrapper that opens a fresh DB session and closes it.
- Jobs are intentionally coarse (every 5 minutes / daily) — Phase 4 does not
  need second-level precision.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger("scheduler.runner")

_scheduler = None
_session_factory: Optional[Callable] = None


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _make_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.loader import load_config
    from database.models import Base

    engine = create_engine(load_config().database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _tick_refresh_tokens():
    from scheduler.job import refresh_expiring_tokens
    try:
        results = refresh_expiring_tokens(_session_factory or _make_session)
        if results:
            logger.info("token refresh tick processed %d tokens", len(results))
    except Exception:
        logger.exception("token refresh tick failed")


def _tick_expire_subscriptions():
    from scheduler.job import expire_overdue_subscriptions
    try:
        summary = expire_overdue_subscriptions(_session_factory or _make_session)
        if summary.get("expired", 0):
            logger.info("expire tick marked %d subscriptions expired", summary["expired"])
    except Exception:
        logger.exception("expire tick failed")


def _tick_monthly_gifts():
    from benefits.service import generate_monthly_gifts
    try:
        session = (_session_factory or _make_session)()
        try:
            created = generate_monthly_gifts(session)
            if created:
                logger.info("monthly-gift tick issued %d coupons", len(created))
        finally:
            session.close()
    except Exception:
        logger.exception("monthly-gift tick failed")


def _tick_trial_reminders():
    """Send trial-expiring reminder to every merchant whose trial ends in
    exactly `TRIAL_REMINDER_DAYS` days (default 3). Idempotent — the email
    layer logs each send, downstream de-duplication belongs to the email
    provider."""
    from notifications.trial_reminder import find_merchants_to_remind, send_reminder

    days_threshold = int(os.getenv("TRIAL_REMINDER_DAYS", "3"))
    try:
        session = (_session_factory or _make_session)()
        try:
            merchants = find_merchants_to_remind(session, days_threshold=days_threshold)
            for merchant in merchants:
                try:
                    send_reminder(merchant)
                except Exception:
                    logger.exception("trial reminder failed for merchant %s", merchant.id)
            if merchants:
                logger.info("trial-reminder tick notified %d merchants", len(merchants))
        finally:
            session.close()
    except Exception:
        logger.exception("trial-reminder tick failed")


def start(session_factory: Optional[Callable] = None) -> None:
    """Install the background scheduler. Safe no-op if unavailable."""
    global _scheduler, _session_factory
    if _scheduler is not None:
        return

    if not _as_bool(os.getenv("SCHEDULER_ENABLED"), default=True):
        logger.info("SCHEDULER_ENABLED=false — skipping scheduler startup")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.info("apscheduler not installed — skipping scheduler startup")
        return

    _session_factory = session_factory
    scheduler = BackgroundScheduler(timezone=os.getenv("SCHEDULER_TIMEZONE", "UTC"))
    scheduler.add_job(_tick_refresh_tokens, "interval", minutes=5, id="refresh_expiring_tokens")
    scheduler.add_job(_tick_trial_reminders, "cron", hour=9, id="trial_reminders")
    scheduler.add_job(_tick_expire_subscriptions, "cron", hour=2, id="expire_subscriptions")
    scheduler.add_job(_tick_monthly_gifts, "cron", day=1, hour=3, id="monthly_gifts")
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "scheduler started: refresh_expiring_tokens (5m), "
        "trial_reminders (daily 09:00), expire_subscriptions (daily 02:00), "
        "monthly_gifts (day=1 03:00)"
    )


def stop() -> None:
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    except Exception:
        pass
    _scheduler = None
