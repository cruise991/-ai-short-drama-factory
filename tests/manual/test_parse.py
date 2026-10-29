import json
with open('projects/单集视频_C005_Lili/runs/20260804_074656/01_storyboards_scripts/01_storyboard.md', 'r') as f:
    text = f.read()
    json_text = text.replace('```json\n', '').replace('\n```', '')
    data = json.loads(json_text)
    stage_1 = data.get("stage_1_image", {})
    stage_2 = data.get("stage_2_video", {})
    timeline = stage_2.get("timeline", [])
    
    locks = stage_1
    locks["video_prompt"] = stage_2.get("video_prompt", "")
    locks["loop_pattern"] = stage_2.get("loop_pattern", "")
    
    for shot in timeline:
        shot["video_prompt"] = stage_2.get("video_prompt", "")
        print(f"Shot {shot.get('shot')}: reference_image = {shot.get('reference_image', 'NONE')}")
