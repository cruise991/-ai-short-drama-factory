"""
Acoustic Enhancement & Spatial Reverb Engine (空间声学与智能侧链闪避引擎)
Integrated from VoiceStudio & Broadcast-Grade Mixing Paradigms:
1. Spatial Impulse & Acoustic Environments (写字楼大堂、雨夜室外、豪车内部、专业演播厅)
2. BGM Dynamic Sidechain Ducking (基于人声包络的 BGM 侧链闪避，确保对白清晰穿透)
3. Emotion-Aware Acoustic Matching (基于场景标签与剧情氛围的自适应环境渲染)
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

class AcousticEnhancer:
    """
    影视级声学环境与空间混响处理器
    """

    # 预设声学空间环境与 FFmpeg 混响滤镜链
    ACOUSTIC_PRESETS = {
        "studio_dry": {
            "name": "演播室干音 (近讲纯净)",
            "description": "极少反射，近场高保真对白，适合旁白解说与近景特写",
            "filter": "equalizer=f=3000:width_type=o:w=1.0:g=1.8"
        },
        "cinematic_reverb": {
            "name": "微混响电影原声 (自然空间)",
            "description": "轻微自然混响，赋予台词立体空气感，消除机械冰冷感",
            "filter": "aecho=0.8:0.8:30:0.22"
        },
        "lobby": {
            "name": "写字楼挑高大堂 (宽广冷峻)",
            "description": "多重早后期反射，高频轻微衰减，突出霸总职场、豪门大厅冷峻感",
            "filter": "aecho=0.85:0.8:40|90:0.35|0.2,lowpass=f=9000"
        },
        "rainy_night": {
            "name": "雨夜街头 (开阔旷远)",
            "description": "开阔室外反射伴随低频滤除，营造深夜、街角、孤寂或复仇对白",
            "filter": "aecho=0.8:0.75:65|130:0.28|0.15,highpass=f=120"
        },
        "luxury_car": {
            "name": "豪车密闭空间 (紧凑低沉)",
            "description": "超短延时微反射，车厢吸音特征，凸显密谋、耳语与私密对峙",
            "filter": "aecho=0.75:0.65:18|35:0.18|0.08,lowpass=f=7500,equalizer=f=200:width_type=o:w=1.0:g=2.0"
        },
        "corridor": {
            "name": "幽深走廊/电梯厅 (回音共振)",
            "description": "中频回旋共振，适合追逐、对峙与悬疑情节",
            "filter": "aecho=0.88:0.82:50|100|150:0.4|0.25|0.12"
        }
    }

    @classmethod
    def apply_spatial_acoustics(
        cls,
        input_audio: str,
        output_audio: str,
        environment: str = "cinematic_reverb"
    ) -> bool:
        """
        为输入对白音频添加空间声学环境混响
        """
        in_p = Path(input_audio)
        out_p = Path(output_audio)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not in_p.exists():
            print(f"[AcousticEnhancer] Input file not found: {input_audio}")
            return False

        preset = cls.ACOUSTIC_PRESETS.get(environment, cls.ACOUSTIC_PRESETS["cinematic_reverb"])
        reverb_filter = preset["filter"]

        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(in_p),
            "-af", reverb_filter,
            "-ar", "48000",
            "-ac", "2",
            str(out_p)
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and out_p.exists():
                return True
            print(f"[AcousticEnhancer] FFmpeg spatial filter error: {res.stderr}")
            return False
        except Exception as e:
            print(f"[AcousticEnhancer] Spatial processing exception: {e}")
            return False

    @classmethod
    def sidechain_duck_bgm(
        cls,
        voice_audio: str,
        bgm_audio: str,
        output_audio: str,
        ducking_db: float = -14.0,
        release_ms: int = 350,
        voice_volume: float = 1.0,
        bgm_base_volume: float = 0.35
    ) -> bool:
        """
        使用 FFmpeg sidechaincompress 滤镜实现专业人声避让 (Ducking):
        当对白出现时，BGM 瞬时下潜 ducking_db (默认 -14dB)，对白结束后 release_ms 毫秒平滑恢复。
        """
        v_p = Path(voice_audio)
        b_p = Path(bgm_audio)
        out_p = Path(output_audio)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not v_p.exists() or not b_p.exists():
            print(f"[AcousticEnhancer] Voice or BGM file missing: {voice_audio}, {bgm_audio}")
            return False

        # sidechaincompress 滤镜图
        # 输入 0: 人声, 输入 1: BGM
        # [1:a] volume=bgm_base_volume [bgm_init];
        # [bgm_init][0:a] sidechaincompress=threshold=0.08:ratio=4:attack=20:release=350 [ducked_bgm];
        # [0:a] volume=voice_volume [v_boost];
        # [ducked_bgm][v_boost] amix=inputs=2:duration=first:dropout_transition=2 [out]
        filter_complex = (
            f"[1:a]volume={bgm_base_volume}[bgm_init];"
            f"[bgm_init][0:a]sidechaincompress=threshold=0.07:ratio=4.5:attack=25:release={release_ms}[ducked_bgm];"
            f"[0:a]volume={voice_volume}[v_boost];"
            f"[ducked_bgm][v_boost]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(v_p),
            "-i", str(b_p),
            "-filter_complex", filter_complex,
            "-map", "[aout]",
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "aac",
            "-b:a", "192k",
            str(out_p)
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and out_p.exists():
                return True
            print(f"[AcousticEnhancer] Sidechain ducking error: {res.stderr}")
            return False
        except Exception as e:
            print(f"[AcousticEnhancer] Sidechain ducking exception: {e}")
            return False

    @classmethod
    def match_acoustic_preset(cls, scene_description: str, mood: str = "") -> str:
        """
        根据场景描述或情绪标签智能推断最佳声学混响空间
        """
        desc_lower = (scene_description + " " + mood).lower()

        if any(w in desc_lower for w in ["车", "豪车", "劳斯莱斯", "迈巴赫", "驾驶", "车内", "私密"]):
            return "luxury_car"
        if any(w in desc_lower for w in ["大堂", "宴会", "公司", "办公室", "大厅", "顶楼", "高档酒店", "走道"]):
            return "lobby"
        if any(w in desc_lower for w in ["雨", "夜", "街头", "马路", "小巷", "天台", "外景", "荒野"]):
            return "rainy_night"
        if any(w in desc_lower for w in ["走廊", "楼梯", "电梯", "地下室", "废弃"]):
            return "corridor"
        if any(w in desc_lower for w in ["解说", "旁白", "科普", "教程"]):
            return "studio_dry"

        return "cinematic_reverb"
