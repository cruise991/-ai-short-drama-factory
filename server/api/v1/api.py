from fastapi import APIRouter
from api.routes import auth, config, projects, dance, avatar, product, knowledge, live

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(config.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(dance.router)
api_v1_router.include_router(avatar.router)
api_v1_router.include_router(product.router)
api_v1_router.include_router(knowledge.router)
api_v1_router.include_router(live.router)

@api_v1_router.get("/health", tags=["system"])
def v1_health():
    return {
        "status": "ok",
        "version": "v1.0.0",
        "api_standard": "RESTful v1",
        "message": "AI Short Drama & Dance API v1 is operational"
    }
