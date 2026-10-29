"""
visual_focus_router.py — 视觉焦点接力与转场匹配路由算法
依据「超级峰视频设计方法论」
"""

from typing import Tuple, Dict
from shared_tools.video_design.storyboard_schema import VisualFocusPosition, TransitionType

FOCUS_COORDINATES: Dict[VisualFocusPosition, Tuple[float, float]] = {
    "top_left": (0.2, 0.2),
    "top_center": (0.5, 0.2),
    "top_right": (0.8, 0.2),
    "center_left": (0.2, 0.5),
    "center": (0.5, 0.5),
    "center_right": (0.8, 0.5),
    "bottom_left": (0.2, 0.8),
    "bottom_center": (0.5, 0.8),
    "bottom_right": (0.8, 0.8)
}

def resolve_focus_relay(exit_focus: VisualFocusPosition, camera_movement: str) -> Tuple[VisualFocusPosition, TransitionType]:
    cam = camera_movement.lower()
    
    if "pan_right" in cam or "whip_pan_right" in cam:
        return "center_left", "whip_pan_right"
    elif "pan_left" in cam or "whip_pan_left" in cam:
        return "center_right", "whip_pan_left"
    elif "push_in" in cam:
        return "center", "push_in"
    elif "pull_out" in cam:
        return "top_center", "cross_dissolve"
    elif "tilt_up" in cam:
        return "bottom_center", "cut"
    elif "crane_down" in cam or "tilt_down" in cam:
        return "top_center", "cut"
    else:
        if exit_focus == "center":
            return "center", "cut"
        return exit_focus, "match_cut"

def validate_focus_continuity(exit_focus: VisualFocusPosition, entry_focus: VisualFocusPosition, transition: TransitionType) -> Tuple[bool, str]:
    x1, y1 = FOCUS_COORDINATES[exit_focus]
    x2, y2 = FOCUS_COORDINATES[entry_focus]
    dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    if dist > 0.5 and transition == "cut":
        return False, f"视觉眼跳预警: 从 {exit_focus} 硬切至 {entry_focus} (跳变跨度 {dist:.2f} > 0.50)，建议改为 whip_pan 或 cross_dissolve 转场接力"
    
    return True, "视线焦点平滑对齐"

