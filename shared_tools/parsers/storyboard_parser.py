import re
import os

def parse_storyboard(markdown_content):
    """
    Parses storyboard markdown into a structured list of shots.
    Each shot contains: id, title, image_suggestion, voiceover, and video_prompt.
    """
    shots = []
    
    # Split by shot headers (e.g. ## Shot 1: ...)
    shot_blocks = re.split(r'^##\s+(Shot\s+\d+.*)$', markdown_content, flags=re.MULTILINE)
    
    # shot_blocks[0] is preamble, so we iterate from 1
    for i in range(1, len(shot_blocks), 2):
        if i + 1 >= len(shot_blocks):
            break
            
        header = shot_blocks[i].strip()
        body = shot_blocks[i+1].strip()
        
        # Extract ID (e.g. "shot_01")
        match_id = re.search(r'Shot\s+(\d+)', header)
        shot_id_num = match_id.group(1).zfill(2) if match_id else "01"
        shot_id = f"shot_{shot_id_num}"
        
        shot_data = {
            "id": shot_id,
            "header": header,
            "image_suggestion": "",
            "voiceover": "",
            "video_prompt": ""
        }
        
        # Extract Image Suggestion
        img_sugg_match = re.search(r'\*\*图像建议\s*\(\s*Image\s*Suggestion\s*\)\*\*\s*[:：]\s*(.*?)(?=\n\*\*|$)', body, re.DOTALL | re.IGNORECASE)
        if img_sugg_match:
            shot_data["image_suggestion"] = img_sugg_match.group(1).strip()
            
        # Extract Voiceover / Dialogue
        vo_match = re.search(r'\*\*(?:旁白|台词)\s*\(\s*(?:Voiceover|Dialogue)\s*\)\*\*\s*[:：]\s*(.*?)(?=\n\*\*|$)', body, re.DOTALL | re.IGNORECASE)
        if vo_match:
            vo_text = vo_match.group(1).strip()
            # Remove quotes
            vo_text = re.sub(r'^[“"”\']|[“"”\']$', '', vo_text)
            shot_data["voiceover"] = vo_text
            shot_data["dialogue"] = vo_text
            
        # Extract Shot Type
        type_match = re.search(r'\*\*(?:分镜类型|类型)\s*\(\s*(?:Shot\s*Type|Type)\s*\)\*\*\s*[:：]\s*(.*?)(?=\n\*\*|$)', body, re.DOTALL | re.IGNORECASE)
        if type_match:
            shot_data["shot_type"] = type_match.group(1).strip()
        elif "手绘" in body or "白板" in body or "handdraw" in body.lower():
            shot_data["shot_type"] = "handdraw"
            
        # Extract Time Range
        time_match = re.search(r'\*\*时间范围\s*(?:\(\s*Time\s*Range\s*\))?\*\*\s*[:：]\s*(.*?)(?=\n\*\*|$)', body, re.DOTALL | re.IGNORECASE)
        if time_match:
            shot_data["time_range"] = time_match.group(1).strip()
            
        # Extract Video Prompt
        prompt_match = re.search(r'\*\*提示词\s*\(\s*Video\s*Prompt\s*\)\*\*\s*[:：]\s*(.*?)(?=\n##|$)', body, re.DOTALL | re.IGNORECASE)
        if prompt_match:
            shot_data["video_prompt"] = prompt_match.group(1).strip()
            
        shots.append(shot_data)
        
    return shots


import json

def parse_timeline_json(data):
    shots = []
    shot_list = data.get("timeline", []) or data.get("shots", [])
    for shot in shot_list:
        shot_id = shot.get("id", f"shot_{len(shots)+1:02d}")
        # Branch 3 outputs visual_prompt. Branch 1/2 outputs camera and base_motion_source.
        img_sugg = shot.get("visual_prompt", shot.get("image_suggestion", ""))
        vid_prmpt = shot.get("video_prompt", "")
        if not vid_prmpt:
            if "camera" in shot or "base_motion_source" in shot:
                vid_prmpt = str(shot.get("camera", "")) + " " + str(shot.get("base_motion_source", ""))
            else:
                vid_prmpt = img_sugg  # Fallback for Branch 3 where visual_prompt is the full prompt

        shots.append({
            "id": shot_id,
            "header": f"## Shot {len(shots)+1}: {shot.get('phase', shot.get('type', 'Unknown'))}",
            "image_suggestion": img_sugg,
            "voiceover": shot.get("voiceover", ""),
            "dialogue": shot.get("dialogue", ""),
            "video_prompt": vid_prmpt.strip(),
            "time_range": shot.get("time_range", str(shot.get("duration", ""))),
            "bgm_id": shot.get("bgm_id", "")
        })
    return data.get("locks", {}), shots

def parse_dance_json(data):
    stage_1 = data.get("stage_1_image", {})
    stage_2 = data.get("stage_2_video", {})
    locks = {
        "character_anchor": data.get("character", ""),
        "costume_lock": stage_1.get("costume", ""),
        "scene_lock": stage_1.get("scene", "")
    }
    
    timeline = stage_2.get("timeline", [])
    if timeline:
        first_t_shot = timeline[0]
        first_vid_prompt = f"{first_t_shot.get('action_prompt', '')}. {first_t_shot.get('camera_prompt', '')}. {stage_2.get('video_prompt', '')}"
        shots = [
            {
                "id": "shot_01",
                "phase": "Anchor_Image_And_First_Dance",
                "image_suggestion": stage_1.get("prompt", ""),
                "video_prompt": first_vid_prompt
            }
        ]
        for i, t_shot in enumerate(timeline[1:]):
            shot_id = f"shot_{str(i+2).zfill(2)}"
            vid_prompt = f"{t_shot.get('action_prompt', '')}. {t_shot.get('camera_prompt', '')}. {stage_2.get('video_prompt', '')}"
            phase = t_shot.get("phase", t_shot.get("type", "Main_Dance"))
            shots.append({
                "id": shot_id,
                "phase": phase,
                "image_suggestion": "",
                "video_prompt": vid_prompt,
                "time_range": f"0:00 - 0:{t_shot.get('duration', 5)}"
            })
    else:
        shots = [
            {
                "id": "shot_01",
                "phase": "Anchor_Image",
                "image_suggestion": stage_1.get("prompt", ""),
                "video_prompt": ""
            },
            {
                "id": "shot_02",
                "phase": "Main_Dance",
                "image_suggestion": "",
                "video_prompt": stage_2.get("video_prompt", ""),
                "time_range": f"0:00 - 0:{data.get('total_duration', 12)}"
            }
        ]
    return locks, shots

def load_and_parse(filepath):
    if not os.path.exists(filepath):
        print(f"[Parser Error] Storyboard file not found: {filepath}")
        return {}, []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    json_content = json_match.group(1) if json_match else content

    try:
        data = json.loads(json_content)
        if "timeline" in data or "shots" in data:
            return parse_timeline_json(data)
        elif "stage_1_image" in data and "stage_2_video" in data:
            return parse_dance_json(data)
    except Exception:
        pass
        
    # Fallback to markdown parsing (no locks available)
    return {}, parse_storyboard(content)

if __name__ == "__main__":
    # Test logic
    test_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            "projects/paperai-series/episode-01/01_storyboards_scripts/01_storyboard.md")
    locks, shots = load_and_parse(test_path)
    import json
    print(json.dumps({"locks": locks, "shots": shots}, indent=2, ensure_ascii=False))
