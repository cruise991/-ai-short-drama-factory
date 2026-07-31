import os
import json
import re
from shared_tools.parsers.storyboard_parser import load_and_parse

LIBLIB_QUALITY_TAGS = "masterpiece, best quality, ultra-detailed, 8k resolution, cinematic lighting, photorealistic"
LIBLIB_NEGATIVE_PROMPT = "blurry, low quality, distortion, bad anatomy, deformed limbs, duplicate face, watermark"

def convert_storyboard_to_libtv_spec(storyboard_path, output_spec_path=None):
    """
    Reads 01_storyboard.md and converts it to a structured .libtv-spec.json package
    for LibLib.tv Web Canvas import or API rendering.
    """
    if not os.path.exists(storyboard_path):
        raise FileNotFoundError(f"Storyboard file not found at {storyboard_path}")
        
    locks, shots = load_and_parse(storyboard_path)
    
    if not shots:
        print(f"[LibTV Spec] WARNING: No shots parsed from {storyboard_path}. Aborting spec generation.")
        return None
    
    spec_data = {
        "version": "1.0",
        "engine": "LibLib.tv",
        "storyboard_source": os.path.basename(storyboard_path),
        "total_shots": len(shots),
        "global_quality_tags": LIBLIB_QUALITY_TAGS,
        "global_negative_prompt": LIBLIB_NEGATIVE_PROMPT,
        "scenes": []
    }
    
    for idx, shot in enumerate(shots, 1):
        raw_prompt = shot.get("video_prompt") or shot.get("image_suggestion") or ""
        
        # Inject LibLib quality tags if not present
        enhanced_prompt = raw_prompt.strip()
        if "masterpiece" not in enhanced_prompt.lower():
            enhanced_prompt = f"{LIBLIB_QUALITY_TAGS}, {enhanced_prompt}"
            
        # Detect camera movements
        camera_tag = "Static Shot"
        if re.search(r'推|push|zoom in', raw_prompt, re.I):
            camera_tag = "Push In Slow"
        elif re.search(r'拉|pull|zoom out', raw_prompt, re.I):
            camera_tag = "Pull Back"
        elif re.search(r'移|摇|pan|tilt', raw_prompt, re.I):
            camera_tag = "Pan / Tilt Motion"
            
        scene_item = {
            "shot_id": shot.get("id", f"shot_{idx:02d}"),
            "header": shot.get("header", f"Shot {idx}"),
            "voiceover": shot.get("voiceover", ""),
            "camera_motion": camera_tag,
            "raw_prompt": raw_prompt,
            "enhanced_prompt": enhanced_prompt,
            "negative_prompt": LIBLIB_NEGATIVE_PROMPT,
            "aspect_ratio": "9:16",
            "suggested_duration_sec": 15,
            "liblib_canvas_import_snippet": {
                "node_type": "VideoGenerationNode",
                "prompt": enhanced_prompt,
                "aspect_ratio": "9:16",
                "camera_motion": camera_tag
            }
        }
        spec_data["scenes"].append(scene_item)
        
    if output_spec_path is None:
        output_spec_path = os.path.join(os.path.dirname(storyboard_path), "01_libtv_spec.json")
        
    with open(output_spec_path, 'w', encoding='utf-8') as f:
        json.dump(spec_data, f, ensure_ascii=False, indent=2)
        
    return output_spec_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        spec_path = convert_storyboard_to_libtv_spec(sys.argv[1])
        print(f"[LibLib Spec Formatter] Generated spec file at: {spec_path}")
