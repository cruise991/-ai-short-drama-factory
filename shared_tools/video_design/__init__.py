"""
shared_tools/video_design — 视频设计与代码逐帧动效核心库
集成超级峰视频设计方法论与 vibe-knowledge 代码成片引擎
"""

from .storyboard_schema import (
    TimecodedBeatSpec, DirectorShot, AudioVisualSyncRule,
    VisualFocusPosition, TransitionType, MusicalSection
)
from .visual_focus_router import (
    resolve_focus_relay, validate_focus_continuity, FOCUS_COORDINATES
)
from .beat_rhythm_engine import (
    calculate_shot_timing_from_bpm, estimate_word_budget,
    generate_director_storyboard, re_roll_single_shot
)
from .code_motion_producer import (
    CodeMotionRenderer, verify_motion_video_quality
)

__all__ = [
    "TimecodedBeatSpec",
    "DirectorShot",
    "AudioVisualSyncRule",
    "VisualFocusPosition",
    "TransitionType",
    "MusicalSection",
    "resolve_focus_relay",
    "validate_focus_continuity",
    "FOCUS_COORDINATES",
    "calculate_shot_timing_from_bpm",
    "estimate_word_budget",
    "generate_director_storyboard",
    "re_roll_single_shot",
    "CodeMotionRenderer",
    "verify_motion_video_quality"
]

