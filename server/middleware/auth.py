from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from core.security import decode_access_token

AUTH_WHITELIST_PREFIXES = [
    "/api/auth",
    "/api/v1/auth",
    "/api/health",
    "/api/v1/health",
    "/healthz",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/media",
    "/ws",
    "/api/v1/tts",
    "/api/dance",
    "/static/poses",
]

class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Global JWT authentication middleware.
    Protects all /api/* routes except whitelisted public endpoints.
    Injects valid token payload into request.state.user.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Optionally decode token if provided (e.g. for tenant-aware public routes)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            payload = decode_access_token(token)
            if payload:
                request.state.user = payload

        # 1. Allow Whitelisted endpoints
        for prefix in AUTH_WHITELIST_PREFIXES:
            if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
                return await call_next(request)

        # Allow internal pipeline inter-process communication
        if path.endswith("/internal_wait_input"):
            return await call_next(request)

        # 2. Non-API endpoints pass through (static files, proxy, etc.)
        if not path.startswith("/api"):
            return await call_next(request)

        # 3. Allow CORS OPTIONS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # 4. Enforce Bearer Token for non-whitelisted API routes
        if not hasattr(request.state, "user"):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "未提供有效身份认证凭据，请登录后重试 (Bearer Token Required)",
                    "detail": "Missing or invalid Authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        return await call_next(request)
