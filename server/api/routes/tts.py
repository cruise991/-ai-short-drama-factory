import os
import logging
import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger("TTSApiRoute")
router = APIRouter(prefix="/tts", tags=["tts"])

# 指向宿主机 TTS 服务（在容器内访问 host.docker.internal:8028）
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://host.docker.internal:8028")

class TTSPreviewReq(BaseModel):
    text: str = Field(..., max_length=2000, description="试听文本")
    voice: Optional[str] = Field(default=None, description="音色ShortName")
    profile_id: Optional[str] = Field(default=None, description="固定角色声纹Profile ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)

class TTSSynthesizeReq(BaseModel):
    text: str = Field(..., max_length=3000, description="合成文本")
    voice: Optional[str] = Field(default=None, description="音色ShortName")
    profile_id: Optional[str] = Field(default=None, description="固定角色声纹Profile ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)

@router.get("/health")
async def tts_health():
    """检查后端与宿主机 TTS 服务的网络健康状态"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{TTS_SERVICE_URL}/health")
            if resp.status_code == 200:
                return {"gateway_status": "ok", "host_tts": resp.json(), "upstream_url": TTS_SERVICE_URL}
    except Exception as e:
        logger.warning(f"Failed to connect to host TTS at {TTS_SERVICE_URL}: {e}")
    return {"gateway_status": "degraded", "upstream_url": TTS_SERVICE_URL, "error": "Host TTS service unreachable"}

@router.get("/voices")
async def list_available_voices():
    """获取所有可用音色列表"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{TTS_SERVICE_URL}/voices")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch voices from TTS upstream: {e}")
    # 兜底返回默认精选列表
    return [
        {"voice_id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (温柔女声/推荐)", "locale": "zh-CN", "gender": "Female"},
        {"voice_id": "zh-CN-YunxiNeural", "name": "云希 (活力男声/热血)", "locale": "zh-CN", "gender": "Male"},
        {"voice_id": "zh-CN-YunjianNeural", "name": "云健 (稳重男声/解说)", "locale": "zh-CN", "gender": "Male"},
        {"voice_id": "zh-CN-XiaoyiNeural", "name": "晓伊 (多情感女声/甜美)", "locale": "zh-CN", "gender": "Female"}
    ]

@router.get("/profiles")
async def list_voice_profiles():
    """获取已固化的角色专属声纹资产库"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{TTS_SERVICE_URL}/profiles")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch voice profiles: {e}")
    return {}

@router.post("/preview")
async def preview_voice(req: TTSPreviewReq):
    """
    生成真实试听 PCM WAV 音频切片 Base64，供前端播放器即时播放
    """
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(f"{TTS_SERVICE_URL}/preview", json=req.dict())
            if resp.status_code == 200:
                return resp.json()
            else:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except httpx.RequestError as exc:
        logger.error(f"HTTP error requesting host TTS: {exc}")
        raise HTTPException(status_code=502, detail=f"Host TTS service unreachable: {str(exc)}")

@router.post("/synthesize")
async def synthesize_voice(req: TTSSynthesizeReq):
    """
    合成完整分镜/对白音频
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{TTS_SERVICE_URL}/synthesize", json=req.dict())
            if resp.status_code == 200:
                return resp.json()
            else:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except httpx.RequestError as exc:
        logger.error(f"HTTP error requesting host TTS: {exc}")
        raise HTTPException(status_code=502, detail=f"Host TTS service unreachable: {str(exc)}")
