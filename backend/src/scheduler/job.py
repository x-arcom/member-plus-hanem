"""Scheduler job registry + the Phase 3 token-refresh tick.

The Phase 0 version was a pure skeleton. Phase 3 fills in the first real
job: `refresh_expiring_tokens` scans OAuth tokens whose `expires_at` is
within a 5-minute horizon and refreshes them via
`auth.token_refresh.refresh_token_for_merchant`.

The job is a pure function that takes a `now` (for deterministic tests) and
a `session_factory`. In the app it is wired against the real DB engine.
"""
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional


logger = logging.getLogger("scheduler")

DEFAULT_HORIZON_MINUTES = 5


class SchedulerJob:
    def __init__(self, name: str, schedule: str, action: Callable[[], None]):
        self.name = name
        self.schedule = schedule
        self.action = action

    def run(self) -> None:
        self.action()


def refresh_expiring_tokens(
    session_factory: Callable[[], object],
    now: Optional[datetime] = None,
    horizon_minutes: int = DEFAULT_HORIZON_MINUTES,
    refresh_fn: Optional[Callable] = None,
) -> List[Dict]:
    """Refresh every OAuth token within `horizon_minutes` of expiry.

    Returns a list of per-merchant results: each either
      {"merchant_id": ..., "status": "refreshed"} or
      {"merchant_id": ..., "status": "failed", "error": "..."}.
    """
    from database.models import OAuthToken
    from auth.token_refresh import refresh_token_for_merchant, TokenRefreshError

    now = now or datetime.utcnow()
    cutoff = now + timedelta(minutes=horizon_minutes)
    refresh = refresh_fn or refresh_token_for_merchant

    db = session_factory()
    results: List[Dict] = []
    try:
        expiring = db.query(OAuthToken).filter(OAuthToken.expires_at <= cutoff).all()
        for row in expiring:
            mid = row.merchant_id
            try:
                refresh(db, mid)
                results.append({"merchant_id": mid, "status": "refreshed"})
                logger.info("refreshed token for merchant %s", mid)
            except TokenRefreshError as exc:
                results.append({"merchant_id": mid, "status": "failed", "error": str(exc)})
                logger.warning("failed to refresh token for merchant %s: %s", mid, exc)
    finally:
        db.close()
    return results


GRACE_DAYS_DEFAULT = 3


def expire_overdue_subscriptions(
    session_factory: Callable[[], object],
    now: Optional[datetime] = None,
    grace_days: int = GRACE_DAYS_DEFAULT,
) -> Dict:
    """Phase G lifecycle sweep:

    - `active` past `expires_at` → `grace`, stamps `grace_ends_at = expires_at + grace_days`.
    - `grace` past `grace_ends_at` → `expired`.

    Returns `{"expired": n_full, "grace": n_entered_grace}`.
    """
    from database.models import Member

    now = now or datetime.utcnow()
    db = session_factory()
    to_grace = 0
    to_expired = 0
    try:
        # Active members past their period end → expired (no grace period per user rule)
        rows = (
            db.query(Member)
            .filter(
                Member.status == "active",
                Member.current_period_end != None,  # noqa: E711
                Member.current_period_end <= now,
            )
            .all()
        )
        for row in rows:
            row.status = "expired"
            to_expired += 1

        if to_expired:
            db.commit()
            logger.info("expire sweep → %d expired", to_expired)
    finally:
        db.close()
    return {"expired": to_expired, "grace": to_grace}


def register_jobs() -> Dict[str, SchedulerJob]:
    """Return the registry of scheduler jobs.

    The jobs themselves need a DB session factory; callers wire that at
    startup. Kept empty here so registration stays explicit (no import-time
    side effects).
    """
    return {}
