from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os

# Default rate limits can be configured via environment
DEFAULT_RATE_LIMIT = os.getenv("DEFAULT_RATE_LIMIT", "120/minute")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT],
    headers_enabled=False
)

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Standardized JSON response when rate limit is exceeded.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "RateLimitExceeded",
            "message": f"请求频率过高，已触发限流保护: {exc.detail}",
            "detail": exc.detail
        }
    )
