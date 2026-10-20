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
]

class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Global JWT authentication middleware.
    Protects all /api/* routes except whitelisted public endpoints.
    Injects valid token payload into request.state.user.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 1. Allow Whitelisted endpoints
        for prefix in AUTH_WHITELIST_PREFIXES:
            if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
                return await call_next(request)

        # 2. Non-API endpoints pass through (static files, proxy, etc.)
        if not path.startswith("/api"):
            return await call_next(request)

        # 3. Allow CORS OPTIONS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # 4. Enforce Bearer Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "未提供身份认证凭据，请登录后重试 (Bearer Token Required)",
                    "detail": "Missing Authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = auth_header[7:].strip()
        payload = decode_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Token 无效或已过期，请重新登录",
                    "detail": "Invalid or expired JWT token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Inject user payload into request.state
        request.state.user = payload
        return await call_next(request)
