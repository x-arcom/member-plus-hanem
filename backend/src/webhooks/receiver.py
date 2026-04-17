from typing import Dict, Optional

from .signature import verify_webhook_signature


def receive_webhook(payload: bytes, signature_header: Optional[str], secret: str) -> Dict[str, object]:
    if not signature_header:
        return {'accepted': False, 'reason': 'missing-signature'}

    if not verify_webhook_signature(payload, signature_header, secret):
        return {'accepted': False, 'reason': 'invalid-signature'}

    # Placeholder: parse and queue webhook events for Phase 1 later.
    return {'accepted': True, 'reason': 'verified'}
