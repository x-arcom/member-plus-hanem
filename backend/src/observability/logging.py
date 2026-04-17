"""Structured JSON logging.

Emits one JSON line per log record, with fields suitable for shipping to a
log aggregator (Loki / CloudWatch / Datadog). Attaches a per-request
`request_id` when middleware is installed.

Usage:
    from observability.logging import configure_logging, RequestIdMiddleware
    configure_logging(environment="production")
    app.add_middleware(RequestIdMiddleware)
"""
import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def current_request_id() -> Optional[str]:
    return _request_id_ctx.get()


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = current_request_id()
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for extra_key in getattr(record, "_extra_keys", ()):
            payload[extra_key] = getattr(record, extra_key)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(environment: str = "development", level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger.

    In `development`, falls back to the classic human-readable format so local
    stack traces stay scannable.
    """
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if environment == "development":
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s — %(message)s"
        ))
    else:
        handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(os.getenv("LOG_LEVEL", level).upper())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a `request_id` to every request, log method/path/status/latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = _request_id_ctx.set(rid)
        start = time.perf_counter()
        logger = logging.getLogger("http")
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            record = logger.makeRecord(
                "http", logging.INFO, __file__, 0,
                "request",
                (), None,
            )
            record._extra_keys = ("method", "path", "status", "latency_ms", "request_id")
            record.method = request.method
            record.path = request.url.path
            record.status = status
            record.latency_ms = elapsed_ms
            record.request_id = rid
            logger.handle(record)
            _request_id_ctx.reset(token)
