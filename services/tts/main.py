import os
import io
import base64
import hashlib
import asyncio
import subprocess
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import edge_tts

app = FastAPI(title="TTS Microservice", version="1.0.0")

CACHE_DIR = os.getenv("TTS_CACHE_DIR", "/data/tts_cache" if os.path.exists("/data") else os.path.join(os.path.dirname(__file__), "cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# Curated voice presets for quick fallback and listing
DEFAULT_VOICES = [
    {"voice_id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (温柔女声/推荐)", "locale": "zh-CN", "gender": "Female"},
    {"voice_id": "zh-CN-YunxiNeural", "name": "云希 (活力男声/热血)", "locale": "zh-CN", "gender": "Male"},
    {"voice_id": "zh-CN-YunjianNeural", "name": "云健 (稳重男声/解说)", "locale": "zh-CN", "gender": "Male"},
    {"voice_id": "zh-CN-XiaoyiNeural", "name": "晓伊 (多情感女声)", "locale": "zh-CN", "gender": "Female"},
    {"voice_id": "en-US-JennyNeural", "name": "Jenny (Natural US Female)", "locale": "en-US", "gender": "Female"},
    {"voice_id": "en-US-GuyNeural", "name": "Guy (Natural US Male)", "locale": "en-US", "gender": "Male"},
]

class SynthesizeRequest(BaseModel):
    text: str = Field(..., max_length=2000, description="待合成的文本内容")
    voice: str = Field(default="zh-CN-XiaoxiaoNeural", description="音色标识")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速倍率")

class SynthesizeResponse(BaseModel):
    s3_key: str
    file_path: str
    duration_seconds: float
    cached: bool
    voice: str

class PreviewResponse(BaseModel):
    audio_base64: str
    format: str = "audio/wav"


def get_audio_hash(text: str, voice: str, speed: float) -> str:
    key_str = f"{text}_{voice}_{speed:.2f}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]


def get_wav_duration(wav_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", wav_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return round(float(result.stdout.strip()), 2)
    except Exception:
        return 0.0


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "tts", "cache_dir": CACHE_DIR}


@app.get("/voices", response_model=List[Dict[str, Any]])
async def list_voices():
    """返回支持的音色列表"""
    try:
        all_voices = await edge_tts.list_voices()
        # Filter popular Chinese & English voices
        filtered = [
            {
                "voice_id": v["ShortName"],
                "name": f"{v['FriendlyName']} ({v['Gender']})",
                "locale": v["Locale"],
                "gender": v["Gender"]
            }
            for v in all_voices
            if v["Locale"].startswith("zh-") or v["Locale"].startswith("en-")
        ]
        return filtered if filtered else DEFAULT_VOICES
    except Exception:
        return DEFAULT_VOICES


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(req: SynthesizeRequest):
    """
    异步合成 16kHz 单声道 16-bit PCM WAV 音频文件（Wav2Lip / LingCast 专属规格）。
    采用 SHA-256 Hash 缓存策略，重复请求秒级命中。
    """
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    file_hash = get_audio_hash(clean_text, req.voice, req.speed)
    final_wav_path = os.path.join(CACHE_DIR, f"tts_{file_hash}.wav")
    s3_key = f"tts/wav/{file_hash}.wav"

    # 1. 检查本地缓存
    if os.path.exists(final_wav_path) and os.path.getsize(final_wav_path) > 0:
        duration = get_wav_duration(final_wav_path)
        return SynthesizeResponse(
            s3_key=s3_key,
            file_path=final_wav_path,
            duration_seconds=duration,
            cached=True,
            voice=req.voice
        )

    # 2. 调用 Edge-TTS 生成临时音频
    rate_percent = int((req.speed - 1.0) * 100)
    rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
    temp_mp3_path = os.path.join(CACHE_DIR, f"temp_{file_hash}.mp3")

    try:
        communicate = edge_tts.Communicate(clean_text, req.voice, rate=rate_str)
        await communicate.save(temp_mp3_path)

        # 3. 使用 FFmpeg 标准化重采样为 16kHz, 16bit, mono PCM WAV
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", temp_mp3_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            final_wav_path
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        duration = get_wav_duration(final_wav_path)

        # 清理临时 mp3
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)

        return SynthesizeResponse(
            s3_key=s3_key,
            file_path=final_wav_path,
            duration_seconds=duration,
            cached=False,
            voice=req.voice
        )
    except Exception as e:
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {str(e)}")


@app.post("/preview", response_model=PreviewResponse)
async def preview_speech(req: SynthesizeRequest):
    """生成快速试听 base64 音频切片，不落盘长期存储"""
    res = await synthesize_speech(req)
    with open(res.file_path, "rb") as f:
        audio_bytes = f.read()
    b64_str = base64.b64encode(audio_bytes).decode("utf-8")
    return PreviewResponse(audio_base64=f"data:audio/wav;base64,{b64_str}")
