"""
Authenticated Salla API client.

Loads the encrypted OAuth token for a merchant, decrypts it per call, and
attaches it as a Bearer token. On a 401 it calls the refresh flow once and
retries the original request.

`transport` is a seam so tests can inject a fake without monkey-patching
`urllib`.
"""
import json
import ssl
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from auth.crypto import decrypt
from auth.token_refresh import refresh_token_for_merchant, TokenRefreshError
from database.models import OAuthToken


class SallaClientError(RuntimeError):
    def __init__(self, message, *, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


@dataclass
class SallaResponse:
    status: int
    body: Dict


# (url, method, body_bytes, headers) -> (status, body_dict)
Transport = Callable[[str, str, Optional[bytes], Dict[str, str]], Tuple[int, Dict]]


def _default_transport(url, method, body, headers) -> Tuple[int, Dict]:
    req = Request(url, data=body, headers=headers, method=method)
    try:
        context = ssl.create_default_context()
        response = urlopen(req, context=context, timeout=15)
        raw = response.read().decode("utf-8") or "{}"
        return response.status, json.loads(raw)
    except HTTPError as http_err:
        try:
            raw = http_err.read().decode("utf-8") or "{}"
            body = json.loads(raw)
        except (ValueError, AttributeError):
            body = {"error": str(http_err)}
        return http_err.code, body
    except (URLError, ValueError) as exc:
        raise SallaClientError(f"Salla transport failed: {exc}")


class SallaClient:
    def __init__(
        self,
        session,
        merchant_id: str,
        transport: Optional[Transport] = None,
        refresh: Optional[Callable[[object, str], Optional[OAuthToken]]] = None,
    ):
        self.db = session
        self.merchant_id = merchant_id
        self._transport = transport or _default_transport
        self._refresh = refresh or refresh_token_for_merchant

    def _current_access_token(self) -> str:
        token = self.db.query(OAuthToken).filter(OAuthToken.merchant_id == self.merchant_id).first()
        if not token:
            raise SallaClientError(f"No OAuth token for merchant {self.merchant_id}", status=404)
        plaintext = decrypt(token.access_token)
        if not plaintext:
            raise SallaClientError("Access token is empty", status=401)
        return plaintext

    def _call(self, method: str, url: str, body: Optional[Dict] = None, *, _retried: bool = False) -> SallaResponse:
        access = self._current_access_token()
        headers = {
            "Authorization": f"Bearer {access}",
            "Accept": "application/json",
        }
        raw_body: Optional[bytes] = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            raw_body = json.dumps(body).encode("utf-8")

        status, data = self._transport(url, method, raw_body, headers)

        if status == 401 and not _retried:
            try:
                self._refresh(self.db, self.merchant_id)
            except TokenRefreshError as exc:
                raise SallaClientError(f"401 and token refresh failed: {exc}", status=401)
            return self._call(method, url, body, _retried=True)

        if status >= 400:
            raise SallaClientError(f"Salla API {method} {url} returned {status}: {data}", status=status)
        return SallaResponse(status=status, body=data)

    def get(self, url: str) -> SallaResponse:
        return self._call("GET", url)

    def post(self, url: str, body: Dict) -> SallaResponse:
        return self._call("POST", url, body)
