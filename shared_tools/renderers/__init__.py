from .base_renderer import BaseRenderer
from .agnes_renderer import AgnesRenderer
from .viggle_renderer import ViggleRenderer

def get_renderer(phase: str, is_dance: bool, config: dict) -> BaseRenderer:
    enable_pose_control = config.get("dance_factory", {}).get("enable_pose_control", False)
    
    if is_dance and enable_pose_control and phase == "Main_Dance":
        return ViggleRenderer()
    
    return AgnesRenderer()
