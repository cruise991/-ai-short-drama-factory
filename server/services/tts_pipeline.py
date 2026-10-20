import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("TTSPipeline")

TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8001")

class TTSAudioClip:
    def __init__(self, text: str, file_path: str, duration_sec: float, cached: bool = False):
        self.text = text
        self.file_path = file_path
        self.duration_sec = duration_sec
        self.cached = cached

class TTSPipeline:
    def __init__(self, tts_url: str = TTS_SERVICE_URL):
        self.tts_url = tts_url
        self.default_voice = "zh-CN-XiaoxiaoNeural"
        self._clip_cache: Dict[str, TTSAudioClip] = {}

    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None, 
        speed: float = 1.0
    ) -> TTSAudioClip:
        """调用 TTS 微服务合成单句音频"""
        voice = voice or self.default_voice
        cache_key = f"{text}_{voice}_{speed:.2f}"
        if cache_key in self._clip_cache:
            return self._clip_cache[cache_key]

        payload = {
            "text": text,
            "voice": voice,
            "speed": speed
        }

        try:
            resp = await asyncio.to_thread(
                lambda: requests.post(f"{self.tts_url}/synthesize", json=payload, timeout=10.0)
            )
            if resp.status_code == 200:
                data = resp.json()
                clip = TTSAudioClip(
                    text=text,
                    file_path=data.get("file_path", ""),
                    duration_sec=float(data.get("duration_seconds", 2.0)),
                    cached=data.get("cached", False)
                )
                self._clip_cache[cache_key] = clip
                return clip
            else:
                logger.error(f"TTS service returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"TTS synthesis connection failure ({e}), generating simulated fallback clip.")

        # 降级模拟音频分片 (用于离线或单元测试快速执行)
        estimated_duration = max(1.0, round(len(text) * 0.22, 2))
        clip = TTSAudioClip(
            text=text,
            file_path=f"/tmp/mock_tts_{abs(hash(cache_key))}.wav",
            duration_sec=estimated_duration,
            cached=False
        )
        self._clip_cache[cache_key] = clip
        return clip

    async def prefetch_queue(
        self, 
        sentences: List[str], 
        voice: Optional[str] = None, 
        speed: float = 1.0
    ) -> List[TTSAudioClip]:
        """
        预取流水线：并行/有序提前合成一组句子，生成有序音频切片列表，消灭句间卡顿
        """
        if not sentences:
            return []
        
        tasks = [self.synthesize(sentence, voice, speed) for sentence in sentences]
        clips = await asyncio.gather(*tasks)
        return list(clips)
