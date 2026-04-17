import hmac
import hashlib
from typing import Optional


def verify_webhook_signature(payload: bytes, signature_header: Optional[str], secret: str) -> bool:
    if not signature_header or not secret:
        return False
    expected = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
