import os
import json
import subprocess
import time
import glob

def render_with_openmontage(workspace_dir, episode_dir, branch_type, videos, beat_drops=None, output_path=None):
    """
    OpenMontage Bridge for rendering
    branch_type: 'short_drama' or 'dance'
    videos: list of video file paths to stitch
    beat_drops: list of timestamps [2.5, 4.0, ...]
    """
    if not output_path:
        output_path = os.path.join(episode_dir, "04_final_output", "final_montage.mp4")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    composer_dir = os.path.join(workspace_dir, "third_party", "OpenMontage", "remotion-composer")
    composition_path = os.path.join(composer_dir, "public", "Composition.json")
    
    # Check if Remotion Composer is actually installed
    if not os.path.isdir(composer_dir):
        print("[Post-Production] Warning: OpenMontage composer not found. Falling back to FFmpeg.")
        return fallback_to_ffmpeg(videos, output_path)
    
    # 补丁 1 & 3: Branch Isolation and BPM Sync
    composition_data = generate_composition_json(videos, branch_type, beat_drops)
    
    try:
        with open(composition_path, "w", encoding="utf-8") as f:
            json.dump(composition_data, f, ensure_ascii=False, indent=2)
            
        print("[Post-Production] Triggering Remotion rendering engine...")
        # 补丁 2: Concurrency & Hardware Acceleration Control
        cmd = [
            "npx", "remotion", "render",
            "Composition",
            output_path,
            "--concurrency", "2",
            "--gl",
            "--log", "info"
        ]
        
        result = subprocess.run(cmd, cwd=composer_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Post-Production] ❌ Remotion crash or OOM: {result.stderr}")
            print("[Post-Production] 🔄 Falling back to FFmpeg...")
            return fallback_to_ffmpeg(videos, output_path)
            
        print("[Post-Production] ✅ Remotion rendering successful!")
        return True
    except Exception as e:
        print(f"[Post-Production] ❌ Unexpected error in Remotion bridge: {e}")
        print("[Post-Production] 🔄 Falling back to FFmpeg...")
        return fallback_to_ffmpeg(videos, output_path)

def generate_composition_json(videos, branch_type, beat_drops):
    
    composition_data = {
        "id": "MainMontage",
        "durationInFrames": 0,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "tracks": []
    }
    
    video_track = {"type": "video", "clips": []}
    current_frame = 0
    
    for idx, vid in enumerate(videos):
        # We assume 30fps and 5s per shot for this mockup
        duration_frames = 150 
        
        clip = {
            "src": os.path.abspath(vid),
            "startFrame": current_frame,
            "durationInFrames": duration_frames,
            "type": "video"
        }
        
        # 补丁 1: Branch Isolation for Transitions
        if branch_type != "dance":
            # For short_drama, add transitions (Crossfade) except for the last clip
            if idx < len(videos) - 1:
                clip["transition"] = {
                    "type": "crossfade",
                    "durationInFrames": 15
                }
                current_frame += (duration_frames - 15)
            else:
                current_frame += duration_frames
        else:
            # 绝对禁止任何转场特效 (No transitions for dance)
            current_frame += duration_frames
            
        video_track["clips"].append(clip)
    
    composition_data["durationInFrames"] = current_frame
    composition_data["tracks"].append(video_track)
    
    # 补丁 3: BPM Beat Sync (Map timestamps to Remotion visual effects track)
    if beat_drops:
        effect_track = {"type": "effects", "events": []}
        for beat_time in beat_drops:
            effect_track["events"].append({
                "type": "camera_shake",
                "startFrame": int(beat_time * 30),
                "durationInFrames": 10
            })
        composition_data["tracks"].append(effect_track)
        
    return composition_data

def fallback_to_ffmpeg(videos, output_path):
    print("[Post-Production] 🛠️ Executing pure FFmpeg concatenation fallback...")
    
    if not videos:
        print("[Post-Production] Error: No videos found for fallback.")
        return False
        
    list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    os.makedirs(os.path.dirname(list_path), exist_ok=True)
    
    with open(list_path, "w", encoding="utf-8") as f:
        for vid in videos:
            f.write(f"file '{os.path.abspath(vid)}'\n")
            
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path, "-c", "copy", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("[Post-Production] ✅ FFmpeg fallback successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Post-Production] ❌ FFmpeg fallback failed: {e.stderr.decode()}")
        return False
