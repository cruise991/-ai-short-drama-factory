import os
import sys
import re
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_SENSITIVE_PATTERNS = [
    (re.compile(r'(Bearer\s+)[A-Za-z0-9_\-\.]{8,}', re.I), r'\1***REDACTED***'),
    (re.compile(r'(sk-[A-Za-z0-9_\-]{8,})', re.I), r'sk-***REDACTED***'),
    (re.compile(r'(wk-[A-Za-z0-9_\-]{8,})', re.I), r'wk-***REDACTED***'),
    (re.compile(r'(password[:=]\s*["\']?)[^"\'\s]+(["\']?)', re.I), r'\1***REDACTED***\2'),
    (re.compile(r'(postgres(?:ql)?:\/\/[^:]+:)[^@]+(@)', re.I), r'\1***REDACTED***\2'),
    (re.compile(r'(redis:\/\/(?::[^@]+@)?)', re.I), r'redis://:***REDACTED***@'),
]

def sanitize_log_content(text: str) -> str:
    """Sanitize sensitive keys, tokens, and database passwords from string."""
    if not text or not isinstance(text, str):
        return text
    for pattern, repl in _SENSITIVE_PATTERNS:
        text = pattern.sub(repl, text)
    return text

class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON objects for structured log aggregation (ELK, Loki, CloudWatch).
    Automatically sanitizes credentials and sensitive values.
    """
    def format(self, record: logging.LogRecord) -> str:
        clean_msg = sanitize_log_content(record.getMessage())
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": clean_msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Inject correlation/request context if present
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "tenant_id"):
            log_obj["tenant_id"] = getattr(record, "tenant_id")
            
        if record.exc_info:
            raw_exc = self.formatException(record.exc_info)
            log_obj["exception"] = sanitize_log_content(raw_exc)
            
        return json.dumps(log_obj, ensure_ascii=False)


def setup_structured_logging(level: str = "INFO"):
    """
    Configure root and application loggers to output structured JSON logs.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing stream handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Reduce noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting X-Request-ID into request scope and logging request lifecycles.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Attach request_id to context
        logger = logging.getLogger("server.request")
        extra = {"request_id": request_id}

        start_time = datetime.utcnow()
        try:
            response: Response = await call_next(request)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000.0
            response.headers["X-Request-ID"] = request_id

            if request.url.path not in ("/healthz", "/metrics"):
                logger.info(
                    f"{request.method} {request.url.path} [{response.status_code}] - {duration_ms:.2f}ms",
                    extra=extra
                )
            return response
        except Exception as exc:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000.0
            logger.error(
                f"Unhandled error in {request.method} {request.url.path} after {duration_ms:.2f}ms: {exc}",
                exc_info=True,
                extra=extra
            )
            raise exc
