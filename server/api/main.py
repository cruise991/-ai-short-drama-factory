import os
import sys
from pathlib import Path

# Ensure root workspace and server directories are accessible in sys.path
for _p in ["/workspace", str(Path(__file__).resolve().parent.parent.parent), str(Path(__file__).resolve().parent.parent)]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from middleware.rate_limit import limiter, rate_limit_handler
from models.database import create_db_and_tables
from ws.logger import manager
from worker.task_runner import worker_loop

# ------------------------------------------------------------------------------
# Modern Lifespan Manager (replaces deprecated @app.on_event)
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase
    create_db_and_tables()
    print("[Lifespan] Database and tables verified.")
    manager.broadcast_sync("[System] 🎬 AI Short Drama & Dance API Backend initialized.")
    manager.broadcast_sync("[System] 📦 Database and tables verified. Storage directories ready.")
    
    worker_task = asyncio.create_task(worker_loop())
    app.state.worker_task = worker_task
    
    yield
    
    # Shutdown phase
    print("[Lifespan] Initiating graceful shutdown of backend services...")
    if hasattr(app.state, "worker_task") and app.state.worker_task:
        app.state.worker_task.cancel()
        try:
            await app.state.worker_task
        except asyncio.CancelledError:
            pass
    manager.broadcast_sync("[System] 🛑 AI Short Drama API Backend shutdown complete.")
    print("[Lifespan] Backend services shutdown completed.")

# ------------------------------------------------------------------------------
# FastAPI Application Instance
# ------------------------------------------------------------------------------
app = FastAPI(
    title="AI Short Drama & Dance API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# Secure CORS configuration
cors_origins_raw = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8008"
)
allowed_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
allow_credentials = False if "*" in allowed_origins else True

from middleware.auth import JWTAuthenticationMiddleware
from core.logging import RequestContextLogMiddleware
from core.metrics import PrometheusMiddleware

app.add_middleware(JWTAuthenticationMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestContextLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Unhandled Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_id = str(uuid.uuid4())
    print(f"[Error] Unhandled exception occurred [Error ID: {error_id}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "系统处理请求时发生内部错误，请稍后重试",
            "detail": str(exc),
            "error_id": error_id
        }
    )

# ------------------------------------------------------------------------------
# Storage Directories
# ------------------------------------------------------------------------------
if os.path.exists("/workspace/out"):
    BASE_DIR = "/workspace"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_DIR = os.path.join(BASE_DIR, "out")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# Router Mounts: v1 Architecture & Legacy Backward Compatibility
# ------------------------------------------------------------------------------
from api.routes import auth, config, projects, ws, dance, avatar, product, knowledge, live, video_design
from api.v1.api import api_v1_router

# 1. Mount API v1 standardized routes (/api/v1/...)
app.include_router(api_v1_router)

# 2. Mount Legacy API routes (/api/...) for backward compatibility
legacy_router = APIRouter(prefix="/api")
legacy_router.include_router(auth.router)
legacy_router.include_router(config.router)
legacy_router.include_router(projects.router)
legacy_router.include_router(dance.router)
legacy_router.include_router(avatar.router)
legacy_router.include_router(product.router)
legacy_router.include_router(knowledge.router)
legacy_router.include_router(live.router)
legacy_router.include_router(video_design.router)
app.include_router(legacy_router)

# 3. Mount WebSocket router
app.include_router(ws.router)

# 4. Mount Static Media Endpoints
app.mount("/media/out", StaticFiles(directory=OUT_DIR), name="media_out")
app.mount("/media/projects", StaticFiles(directory=PROJECTS_DIR), name="media_projects")

POSES_STATIC_DIR = os.path.join(BASE_DIR, "server", "data", "poses")
if not os.path.exists(POSES_STATIC_DIR) and os.path.exists("/app/data/poses"):
    POSES_STATIC_DIR = "/app/data/poses"
os.makedirs(POSES_STATIC_DIR, exist_ok=True)
app.mount("/static/poses", StaticFiles(directory=POSES_STATIC_DIR), name="static_poses")

# ------------------------------------------------------------------------------
# Health Check Endpoints
# ------------------------------------------------------------------------------
@app.get("/api/health", tags=["system"])
def legacy_health_check():
    return {
        "status": "ok",
        "message": "Backend is running",
        "version": "1.0.0"
    }
