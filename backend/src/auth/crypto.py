"""
Symmetric encryption for secrets stored at rest (OAuth tokens, refresh tokens).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package.
Keys are loaded from ENCRYPTION_KEY via config.loader.

All values returned from `encrypt()` are URL-safe base64 strings that include
the Fernet version prefix. `decrypt()` is tolerant of legacy plaintext values
(any value that fails Fernet parse is returned unchanged) so we can roll this
feature out without a forced data migration — callers should re-encrypt values
on next write to migrate them forward.
"""
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config.loader import load_config


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    key = load_config().encryption_key
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is not configured")
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise RuntimeError(f"ENCRYPTION_KEY is not a valid Fernet key: {exc}") from exc


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt a string. Returns None for None input (so it's safe to call on
    nullable model fields)."""
    if plaintext is None:
        return None
    if plaintext == "":
        return ""
    return _cipher().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(value: Optional[str]) -> Optional[str]:
    """Decrypt a Fernet token. If the value isn't a valid Fernet token, assume
    it is legacy plaintext and return it unchanged (forward-compatible rollout).
    Returns None for None input."""
    if value is None:
        return None
    if value == "":
        return ""
    try:
        return _cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return value


def reset_cache() -> None:
    """Force the cipher to re-read the config. Used by tests that change env."""
    _cipher.cache_clear()
