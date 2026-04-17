"""Trial-reminder job: pick merchants to notify and send their email.

Pure functions so they can be unit-tested without the scheduler.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List

from database.models import Merchant


def find_merchants_to_remind(session, days_threshold: int = 3) -> List[Merchant]:
    """Return merchants whose trial ends in <= `days_threshold` days and is
    still active. We intentionally don't filter on "reminded before" — that
    belongs to the email provider's de-duplication. A Phase 5 follow-up can
    add a `trial_reminder_sent_at` column if we see duplicate sends.
    """
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days_threshold)
    return (
        session.query(Merchant)
        .filter(
            Merchant.is_active.is_(True),
            Merchant.trial_active.is_(True),
            Merchant.trial_end_date >= now,      # not already expired
            Merchant.trial_end_date <= cutoff,   # within the window
        )
        .all()
    )


def send_reminder(merchant: Merchant) -> bool:
    """Fire-and-wait the email (runs in a worker thread via APScheduler)."""
    from email_service.service import send_trial_expiring_email

    days_remaining = max(0, (merchant.trial_end_date - datetime.utcnow()).days)
    return asyncio.run(send_trial_expiring_email(
        merchant.merchant_email,
        days_remaining=days_remaining,
        language=merchant.language or "ar",
    ))
