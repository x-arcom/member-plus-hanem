"""
Salla API retry utility — PRD §17.6.

One shared function used everywhere for Salla API calls. Rules:
- 5xx / timeout: 3× with backoff 1s, 2s, 4s
- 429: wait Retry-After header
- 401: force refresh token, retry once
- 404: do NOT retry. Log and throw.
- other 4xx: do NOT retry. Log and throw.
"""
import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger("salla.retry")

T = TypeVar("T")

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]


class SallaAPIError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


def with_retry(
    fn: Callable[[], T],
    on_401_refresh: Callable[[], None] = None,
    label: str = "salla_api_call",
) -> T:
    """Execute `fn` with PRD §17.6 retry rules.

    `fn` should raise `SallaAPIError` with `.status` on HTTP errors.
    `on_401_refresh` is called once on 401 to refresh the OAuth token.
    """
    last_exc = None

    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except SallaAPIError as exc:
            last_exc = exc

            if exc.status == 401 and on_401_refresh and attempt == 0:
                logger.info("%s: 401 — refreshing token and retrying", label)
                try:
                    on_401_refresh()
                except Exception as refresh_err:
                    logger.warning("%s: token refresh failed: %s", label, refresh_err)
                    raise exc from refresh_err
                continue

            if exc.status == 429:
                wait = 5  # default if no Retry-After header
                logger.info("%s: 429 — waiting %ds", label, wait)
                time.sleep(wait)
                continue

            if exc.status >= 500 or exc.status == 0:
                backoff = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                logger.info("%s: %d — retry %d/%d in %ds", label, exc.status, attempt + 1, MAX_RETRIES, backoff)
                time.sleep(backoff)
                continue

            # 404 or other 4xx: do NOT retry
            logger.warning("%s: %d — not retrying", label, exc.status)
            raise

        except Exception as exc:
            # Network timeout or other — treat as 5xx
            last_exc = exc
            backoff = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
            logger.info("%s: exception — retry %d/%d in %ds: %s", label, attempt + 1, MAX_RETRIES, backoff, exc)
            time.sleep(backoff)

    raise last_exc
