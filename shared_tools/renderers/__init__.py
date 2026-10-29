from .base_renderer import BaseRenderer

def get_renderer(phase: str, is_dance: bool, config: dict, shot: dict = None) -> BaseRenderer:
    enable_pose_control = config.get("dance_factory", {}).get("enable_pose_control", False)
    
    # Check if handdraw renderer requested via phase, shot_type or project_type
    shot_type = (shot.get("shot_type") or shot.get("type") or "").lower() if shot else ""
    project_type = config.get("project_type", "").lower()
    
    if phase == "Handdraw" or "handdraw" in shot_type or "whiteboard" in shot_type or project_type in ["handdraw", "sweety_handdraw"]:
        from .handdraw_renderer import HanddrawRenderer
        return HanddrawRenderer()
    
    if is_dance and enable_pose_control and phase == "Main_Dance":
        from .viggle_renderer import ViggleRenderer
        return ViggleRenderer()
    
    from .agnes_renderer import AgnesRenderer
    return AgnesRenderer()

