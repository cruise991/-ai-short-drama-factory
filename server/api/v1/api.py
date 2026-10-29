from fastapi import APIRouter
from api.routes import auth, config, projects, dance, avatar, product, knowledge, live, tts, video_design

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(config.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(dance.router)
api_v1_router.include_router(avatar.router)
api_v1_router.include_router(product.router)
api_v1_router.include_router(knowledge.router)
api_v1_router.include_router(live.router)
api_v1_router.include_router(tts.router)
api_v1_router.include_router(video_design.router)

import time
import os
import urllib.request
import json
from sqlmodel import Session, select, func
from models.database import engine, Project

@api_v1_router.get("/health", tags=["system"])
def v1_health():
    """Comprehensive system health and service diagnostic probe."""
    results = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {},
        "metrics": {}
    }
    
    # 1. Database Check
    try:
        with Session(engine) as session:
            count = session.exec(select(func.count(Project.id))).one()
            results["services"]["database"] = {
                "status": "connected",
                "engine": "sqlite" if str(engine.url).startswith("sqlite") else "postgresql",
                "total_projects": count
            }
    except Exception as e:
        results["services"]["database"] = {"status": "error", "error": str(e)}
        results["status"] = "degraded"

    # 2. Host TTS Service Check
    tts_url = os.getenv("TTS_SERVICE_URL", "http://host.docker.internal:8028")
    t0 = time.time()
    try:
        req = urllib.request.Request(f"{tts_url}/health", headers={"User-Agent": "BackendHealthProbe/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            latency_ms = round((time.time() - t0) * 1000, 1)
            results["services"]["host_tts"] = {
                "status": "online",
                "latency_ms": latency_ms,
                "endpoint": tts_url,
                "details": data
            }
    except Exception as e:
        results["services"]["host_tts"] = {
            "status": "offline_or_unreachable",
            "endpoint": tts_url,
            "error": str(e),
            "fallback": "Standard 16kHz PCM WAV in-container fallback active"
        }
        
    # 3. MinIO Storage Check
    minio_url = os.getenv("MINIO_ENDPOINT", "http://short_drama_minio:9000")
    try:
        req = urllib.request.Request(f"{minio_url}/minio/health/live", headers={"User-Agent": "BackendHealthProbe/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            results["services"]["storage_minio"] = {"status": "online", "code": resp.status}
    except Exception as e:
        results["services"]["storage_minio"] = {"status": "unreachable_or_standalone", "note": str(e)}

    # 4. Storage Directories Writable
    workspace_dir = "/workspace" if os.path.exists("/workspace") else os.getcwd()
    out_dir = os.path.join(workspace_dir, "out")
    projects_dir = os.path.join(workspace_dir, "projects")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(projects_dir, exist_ok=True)
    results["services"]["filesystem"] = {
        "workspace": workspace_dir,
        "out_writable": os.access(out_dir, os.W_OK),
        "projects_writable": os.access(projects_dir, os.W_OK)
    }

    # 5. LLM Keys Scan
    try:
        import sys
        if "/workspace" not in sys.path and os.path.exists("/workspace"):
            sys.path.append("/workspace")
        from shared_tools.api_pool import get_agnes_keys
        keys = get_agnes_keys()
        results["metrics"]["active_llm_keys"] = len(keys)
    except Exception as e:
        results["metrics"]["active_llm_keys"] = 0
        results["metrics"]["llm_scan_note"] = str(e)
    
    return results
