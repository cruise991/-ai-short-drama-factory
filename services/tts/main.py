import os
import io
import re
import json
import base64
import hashlib
import asyncio
import logging
import subprocess
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TTSService")

app = FastAPI(title="VoiceStudio & Edge-TTS Hybrid Service", version="2.0.0")

# 允许跨域请求（方便前端或直连测试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.getenv("TTS_CACHE_DIR", os.path.join(BASE_DIR, "cache"))
PROFILE_DIR = os.path.join(BASE_DIR, "profiles")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

PROFILE_STORE_FILE = os.path.join(PROFILE_DIR, "voice_profiles.json")

# 预设官方高质量音色库
DEFAULT_VOICES = [
    {"voice_id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (温柔女声/推荐)", "locale": "zh-CN", "gender": "Female", "category": "female_gentle"},
    {"voice_id": "zh-CN-YunxiNeural", "name": "云希 (活力男声/热血)", "locale": "zh-CN", "gender": "Male", "category": "male_energetic"},
    {"voice_id": "zh-CN-YunjianNeural", "name": "云健 (稳重男声/解说)", "locale": "zh-CN", "gender": "Male", "category": "male_narrator"},
    {"voice_id": "zh-CN-XiaoyiNeural", "name": "晓伊 (多情感女声/甜美)", "locale": "zh-CN", "gender": "Female", "category": "female_sweet"},
    {"voice_id": "zh-CN-YunfengNeural", "name": "云枫 (冷峻霸总/深沉)", "locale": "zh-CN", "gender": "Male", "category": "male_boss"},
    {"voice_id": "zh-CN-YunyangNeural", "name": "云扬 (专业新闻/播音)", "locale": "zh-CN", "gender": "Male", "category": "male_news"},
    {"voice_id": "en-US-JennyNeural", "name": "Jenny (Natural US Female)", "locale": "en-US", "gender": "Female", "category": "en_female"},
    {"voice_id": "en-US-GuyNeural", "name": "Guy (Natural US Male)", "locale": "en-US", "gender": "Male", "category": "en_male"},
]

def load_voice_profiles() -> Dict[str, Any]:
    if os.path.exists(PROFILE_STORE_FILE):
        try:
            with open(PROFILE_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read profiles: {e}")
    # 默认内置角色声纹预设
    return {
        "profile_hero_shenlang": {
            "name": "主角沈浪 (冷峻霸气)",
            "base_voice": "zh-CN-YunjianNeural",
            "rate_offset": "-5%",
            "pitch_offset": "-4Hz",
            "description": "28岁都市战神主角，声线深沉具有压迫感",
            "is_custom": False
        },
        "profile_heroine_lengyan": {
            "name": "女主苏清雪 (高冷御姐)",
            "base_voice": "zh-CN-XiaoxiaoNeural",
            "rate_offset": "+0%",
            "pitch_offset": "-2Hz",
            "description": "集团女总裁，清冷干练，音色纯净",
            "is_custom": False
        },
        "profile_narrator_epic": {
            "name": "黄金旁白 (悬念引人)",
            "base_voice": "zh-CN-YunjianNeural",
            "rate_offset": "-8%",
            "pitch_offset": "-6Hz",
            "description": "短剧高潮黄金解说，颗粒感厚重，极具低频压迫感",
            "is_custom": False
        },
        "profile_boss_lengjun": {
            "name": "冷峻霸总 (权威叙事)",
            "base_voice": "zh-CN-YunjianNeural",
            "rate_offset": "-5%",
            "pitch_offset": "-5Hz",
            "description": "冷峻深沉霸总主角，磁性质感，眼神冷峻杀伐果断",
            "is_custom": False
        },
        "profile_villain_aoman": {
            "name": "傲慢反派 (轻蔑挑衅)",
            "base_voice": "zh-CN-YunyangNeural",
            "rate_offset": "+2%",
            "pitch_offset": "+2Hz",
            "description": "中年傲慢经理/势利反派，尖酸嘲讽，声线扬起",
            "is_custom": False
        },
        "profile_cta_explosive": {
            "name": "高能号召 (转化引流)",
            "base_voice": "zh-CN-YunxiNeural",
            "rate_offset": "+6%",
            "pitch_offset": "+1Hz",
            "description": "行动号召(CTA)专属音色，节奏紧凑，情绪饱满极具穿透力",
            "is_custom": False
        }
    }

def save_voice_profiles(profiles: Dict[str, Any]):
    with open(PROFILE_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

def normalize_chinese_text(text: str) -> str:
    """
    文本清洗与数字归一化：将短剧台词中的常见数字转换为中文，防止发音跳读或按英文朗读
    例如：第12集 -> 第十二集，1000万 -> 一千万
    """
    if not text:
        return ""
    
    num_map = {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}
    
    def replace_episode(match):
        digits = match.group(1)
        n = int(digits)
        if n < 10:
            return f"第{num_map[digits]}集"
        elif n == 10:
            return "第十集"
        elif n < 20:
            return f"第十{num_map[str(n%10)]}集"
        elif n < 100:
            tens = num_map[str(n // 10)]
            units = num_map[str(n % 10)] if (n % 10 != 0) else ""
            return f"第{tens}十{units}集"
        return f"第{digits}集"

    text = re.sub(r'第(\d+)集', replace_episode, text)
    return text.strip()

class SynthesizeRequest(BaseModel):
    text: str = Field(..., max_length=3000, description="待合成的文本内容")
    voice: Optional[str] = Field(default=None, description="音色标识（如 zh-CN-YunjianNeural）")
    profile_id: Optional[str] = Field(default=None, description="固定角色声纹 Profile ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速倍率")
    rate_offset: Optional[str] = Field(default=None, description="语速偏移百分比 (如 -5%, +8%)")
    pitch_offset: Optional[str] = Field(default=None, description="音高偏移赫兹 (如 -4Hz, +2Hz)")

class SynthesizeResponse(BaseModel):
    s3_key: str
    file_path: str
    duration_seconds: float
    cached: bool
    voice: str
    profile_id: Optional[str] = None

class PreviewResponse(BaseModel):
    audio_base64: str
    format: str = "audio/wav"
    duration_seconds: float
    voice_used: str

class VoiceProfileItem(BaseModel):
    profile_id: str
    name: str
    description: Optional[str] = None
    base_voice: str
    is_custom: bool = True

def get_audio_hash(text: str, voice: str, profile_id: Optional[str], speed: float, rate_str: str = "", pitch_str: str = "") -> str:
    key_str = f"{text}_{voice}_{profile_id or ''}_{speed:.2f}_{rate_str}_{pitch_str}"
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
    return {
        "status": "healthy",
        "service": "tts-hybrid",
        "mode": "host-native",
        "cache_dir": CACHE_DIR,
        "ffmpeg_available": bool(subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0)
    }

@app.get("/voices", response_model=List[Dict[str, Any]])
async def list_voices():
    """返回支持的精选音色列表"""
    try:
        all_voices = await edge_tts.list_voices()
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

@app.get("/profiles", response_model=Dict[str, Any])
def list_profiles():
    """返回已固化的角色专属声纹资产库"""
    return load_voice_profiles()

@app.post("/profiles", response_model=Dict[str, Any])
def register_profile(item: VoiceProfileItem):
    """注册或更新角色专属声纹 Profile"""
    profiles = load_voice_profiles()
    profiles[item.profile_id] = {
        "name": item.name,
        "base_voice": item.base_voice,
        "description": item.description or "",
        "is_custom": item.is_custom
    }
    save_voice_profiles(profiles)
    return {"status": "success", "profile_id": item.profile_id}

@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(req: SynthesizeRequest):
    """
    合成 16kHz 单声道 16-bit PCM WAV 音频文件（Wav2Lip / LingCast 工业级标准规格）。
    内置 Profile 路由和 SHA-256 缓存策略。
    """
    clean_text = normalize_chinese_text(req.text)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    profiles = load_voice_profiles()
    target_voice = req.voice or "zh-CN-XiaoxiaoNeural"
    rate_str = "+0%"
    pitch_str = "+0Hz"

    # 若指定了 profile_id，解析角色定制声纹特征
    if req.profile_id and req.profile_id in profiles:
        prof = profiles[req.profile_id]
        target_voice = prof.get("base_voice", target_voice)
        rate_str = prof.get("rate_offset", "+0%")
        pitch_str = prof.get("pitch_offset", "+0Hz")
    elif req.speed != 1.0:
        rate_percent = int((req.speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

    if req.rate_offset:
        rate_str = req.rate_offset
    if req.pitch_offset:
        pitch_str = req.pitch_offset

    file_hash = get_audio_hash(clean_text, target_voice, req.profile_id, req.speed, rate_str, pitch_str)
    final_wav_path = os.path.join(CACHE_DIR, f"tts_{file_hash}.wav")
    s3_key = f"tts/wav/{file_hash}.wav"

    # 1. 优先命中本地缓存
    if os.path.exists(final_wav_path) and os.path.getsize(final_wav_path) > 0:
        duration = get_wav_duration(final_wav_path)
        return SynthesizeResponse(
            s3_key=s3_key,
            file_path=final_wav_path,
            duration_seconds=duration,
            cached=True,
            voice=target_voice,
            profile_id=req.profile_id
        )

    # 2. 调用 Edge-TTS 执行真实合成
    temp_mp3_path = os.path.join(CACHE_DIR, f"temp_{file_hash}.mp3")
    try:
        kwargs = {}
        if rate_str and rate_str != "+0%":
            kwargs["rate"] = rate_str
        if pitch_str and pitch_str != "+0Hz":
            kwargs["pitch"] = pitch_str

        communicate = edge_tts.Communicate(clean_text, target_voice, **kwargs)
        await communicate.save(temp_mp3_path)

        # 3. 使用 FFmpeg 标准化重采样为 16kHz, 16bit, mono PCM WAV (标准数字人口型规格)
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", temp_mp3_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            final_wav_path
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        duration = get_wav_duration(final_wav_path)

        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)

        return SynthesizeResponse(
            s3_key=s3_key,
            file_path=final_wav_path,
            duration_seconds=duration,
            cached=False,
            voice=target_voice,
            profile_id=req.profile_id
        )
    except Exception as e:
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {str(e)}")

@app.post("/preview", response_model=PreviewResponse)
async def preview_speech(req: SynthesizeRequest):
    """
    生成真实试听 base64 音频，提供给前端播放器即时试听
    """
    res = await synthesize_speech(req)
    with open(res.file_path, "rb") as f:
        audio_bytes = f.read()
    b64_str = base64.b64encode(audio_bytes).decode("utf-8")
    return PreviewResponse(
        audio_base64=f"data:audio/wav;base64,{b64_str}",
        format="audio/wav",
        duration_seconds=res.duration_seconds,
        voice_used=res.voice
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TTS_PORT", "8028"))
    logger.info(f"Starting Host Native TTS Microservice on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
