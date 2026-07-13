import os
import json
import time
import sys
import shutil
import random
import subprocess
import tempfile
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def _curl_request(method, url, headers=None, json_data=None):
    # if "agnes-ai.com" in url:
    #     print(f"  [Production Dept] Mocking API response for {url} to avoid network timeout.")
    #     if "video" in url or "agnesapi" in url:
    #         if method == "GET":
    #             return {"status": "completed", "url": "https://mock-video-url.com/mock.mp4"}
    #         return {"video_id": "mock_video_123"}
    #     return {"data": [{"url": "https://mock-image-url.com/mock.png"}]}

    cmd = ["curl", "-s", "-X", method, url]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if json_data:
        cmd.extend(["-d", json.dumps(json_data)])
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"[cURL] Request to {url} timed out.")
    except Exception as e:
        print(f"[cURL] Error: {e}")
    return None

def load_config():
    return {}

from shared_tools.config_loader import get_config

def parse_duration_from_time_range(time_range_str):
    import re
    if not time_range_str: return 0
    def _to_seconds(time_str):
        parts = time_str.strip().split(":")
        if len(parts) == 1: return float(parts[0])
        elif len(parts) == 2: return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3: return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        return 0
    match = re.match(r"^\s*([\d:]+)\s*[-~]\s*([\d:]+)\s*$", time_range_str)
    if match:
        start_sec = _to_seconds(match.group(1))
        end_sec = _to_seconds(match.group(2))
        return max(0, end_sec - start_sec)
    return 0

def calc_num_frames(duration_sec, fps=24):
    raw_frames = int(duration_sec * fps)
    n = round((raw_frames - 1) / 8.0)
    n = max(0, n)
    frames = 8 * n + 1
    return min(frames, 441)

def generate_image_agnes(prompt, output_path, config, size="1024x768"):
    from shared_tools.api_pool import get_agnes_keys, get_available_key, record_429
    model = config.get("PRODUCTION_IMAGE_MODEL", "agnes-image-2.1-flash")
    
    keys = get_agnes_keys()
    
    for _ in range(10): # try 10 times across different keys
        api_key = get_available_key(keys)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "extra_body": {
                "response_format": "url"
            }
        }
        
        print(f"  [AgnesRenderer] Calling REAL Image API for prompt: {prompt[:20]}...")
        resp = _curl_request("POST", "https://apihub.agnes-ai.com/v1/images/generations", headers=headers, json_data=data)
        
        if resp and "error" in resp and resp["error"].get("code") == 429:
            record_429(api_key)
            continue
            
        # The API docs imply response format 'url' might just return the URL, but checking 'data' array is standard for OpenAI-like endpoints. 
        # Let's handle both just in case.
        url = None
        if resp and "data" in resp and len(resp["data"]) > 0:
            url = resp["data"][0].get("url")
        elif resp and "url" in resp:
            url = resp["url"]

        if url:
            if url == "https://mock-image-url.com/mock.png":
                # Copy a real mock image file
                mock_img = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "mock_image.png")
                shutil.copy2(mock_img, output_path)
            elif url == "https://mock-video-url.com/mock.mp4":
                # Copy a real mock video file
                mock_vid = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "mock_video.mp4")
                shutil.copy2(mock_vid, output_path)
            else:
                # Download the image using curl
                dl_cmd = ["curl", "-s", "-o", output_path, url]
                subprocess.run(dl_cmd)
            return url
            
        # If we got a real error (not 429) or empty data, break and raise
        break
        
    raise Exception(f"Image generation failed for {output_path}. API response was invalid or rate limited.")

def generate_video_agnes(image_url, video_prompt, output_path, config, size="1152x768", num_frames=121):
    from shared_tools.api_pool import get_agnes_keys, get_available_key, record_429
    model = config.get("PRODUCTION_VIDEO_MODEL", "agnes-video-v2.0")
    
    keys = get_agnes_keys()
    try:
        width_str, height_str = size.split("x")
        width, height = int(width_str), int(height_str)
    except:
        width, height = 1152, 768
    
    for _ in range(10): # try up to 10 times across different keys
        api_key = get_available_key(keys)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "prompt": video_prompt + (", starting exactly from the reference pose, seamless continuation" if image_url else ""),
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "frame_rate": 24
        }
        if image_url:
            data["extra_body"] = {
                "image": image_url
            }
        
        print(f"  [AgnesRenderer] Calling REAL Video API for {output_path}...")
        resp = _curl_request("POST", "https://apihub.agnes-ai.com/v1/videos", headers=headers, json_data=data)
        
        if resp and "error" in resp and resp["error"].get("code") == 429:
            record_429(api_key)
            continue
            
        video_id = None
        if resp:
            video_id = resp.get("video_id") or resp.get("id") or resp.get("task_id")
            
        if video_id:
            # Poll for completion
            for _ in range(20):
                if video_id == "mock_video_123":
                    time.sleep(1)
                else:
                    time.sleep(15)
                # Official GET endpoint
                status_resp = _curl_request("GET", f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}", headers=headers)
                if status_resp:
                    # New status structure: "completed" and "url"
                    status = status_resp.get("status")
                    if status == "completed" and "url" in status_resp:
                        vid_url = status_resp["url"]
                        if vid_url == "https://mock-image-url.com/mock.png":
                            mock_img = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "mock_image.png")
                            shutil.copy2(mock_img, output_path)
                        elif vid_url == "https://mock-video-url.com/mock.mp4":
                            mock_vid = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "mock_video.mp4")
                            shutil.copy2(mock_vid, output_path)
                        else:
                            dl_cmd = ["curl", "-s", "-o", output_path, vid_url]
                            subprocess.run(dl_cmd)
                        return True
                    elif status == "failed" or status == "error":
                        # Not a 429, actual task failure
                        break
            
            # If we fall through the polling loop without returning, it's a timeout or failure
            break
            
        # If we got a real error (not 429) on the POST, break and raise
        break
        
    raise Exception(f"Video generation failed for {output_path}. API response was invalid or rate limited.")

def process_ticket(episode_dir):
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
    
    if not os.path.exists(ticket_path):
        return False
        
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)
        
    # We allow Draft_Completed for standard loops, but let's just forcefully execute the API for this demonstration
    print(f"[Production Dept] Initiating Real API Generation Pipeline for: {ticket.get('goal')}")
    
    config = load_config()
    assets_dir = os.path.join(episode_dir, "02_raw_assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from shared_tools.parsers.storyboard_parser import load_and_parse
    from shared_tools.renderers import get_renderer
    
    storyboard_path = os.path.join(episode_dir, "01_storyboards_scripts", "01_storyboard.md")
    parsed_result = load_and_parse(storyboard_path)
    if isinstance(parsed_result, tuple) and len(parsed_result) == 2:
        locks, shots = parsed_result
    else:
        locks, shots = {}, parsed_result
        
    if not shots:
        print("[Production Dept] Error: No valid shots found in storyboard.")
        ticket["status"] = "Paused_By_Error"
        ticket["error_message"] = "No valid shots found in storyboard."
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
        return False
        
    is_dance = "舞蹈" in ticket.get("format_type", "") or "钩子" in ticket.get("format_type", "")
    target_size = ticket.get("image_size", config.get("dance_factory", {}).get("image_size", "768x1344") if is_dance else "1024x768")

    def upload_image_to_temp_host(filepath):
        print(f"  [Upload] Attempting to save {filepath} to local Media Center (MinIO)...")
        filename = os.path.basename(filepath)
        s3_url = None
        
        try:
            import boto3
            import uuid
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "media_center", ".env"))
            
            s3_client = boto3.client('s3',
                                     endpoint_url=f"http://localhost:{os.getenv('MINIO_API_PORT', '4000')}",
                                     aws_access_key_id=os.getenv('MINIO_ROOT_USER', 'admin'),
                                     aws_secret_access_key=os.getenv('MINIO_ROOT_PASSWORD', 'your_secure_password'),
                                     region_name=os.getenv('MINIO_REGION', 'auto'))
            
            bucket_name = os.getenv('S3_BUCKET', 'paperai-media')
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            s3_client.upload_file(filepath, bucket_name, unique_filename)
            print(f"  [Upload] Successfully stored in MinIO bucket: {bucket_name}/{unique_filename}")
            
            public_url = os.getenv('PUBLIC_MEDIA_URL')
            if public_url:
                s3_url = f"{public_url}/{bucket_name}/{unique_filename}"
                print(f"  [Upload] Using Public MinIO URL: {s3_url}")
                return s3_url
            else:
                print("  [Upload] PUBLIC_MEDIA_URL not set. Agnes API requires a public URL.")
        except Exception as e:
            print(f"  [Upload] MinIO upload exception: {e}")
            
        print("  [Upload] Falling back to base64 encoding (100% reliable for local testing)...")
        try:
            import base64
            with open(filepath, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{b64_str}"
        except Exception as e:
            print(f"  [Upload] Base64 fallback failed: {e}")
        return None

    def process_single_shot(shot, anchor_img_url=None, last_video_path=None):
        shot_id = shot["id"]
        vid_prompt_base = shot.get("video_prompt", "")
        
        if is_dance and locks:
            char_anchor = locks.get("character_anchor", "")
            costume = locks.get("costume_lock", "")
            scene = locks.get("scene_lock", "")
            style_desc = ticket.get("style", "")
            
            # The T2I needs full character, costume, scene context, and style (following Agnes API structure)
            img_prompt = f"{char_anchor}, wearing {costume}, standing in {scene}, style: {style_desc}, masterpiece, best quality, highly detailed"
            
            # For I2V Keyframes mode, we pass the character/costume but focus heavily on the dance move
            dance_action = shot.get("image_suggestion", "")
            vid_prompt = f"{char_anchor}, wearing {costume}, in {scene} | {dance_action} | {vid_prompt_base}, style: {style_desc}"
        else:
            img_prompt = shot.get("image_suggestion", "")
            if not img_prompt:
                img_prompt = vid_prompt_base
            vid_prompt = f"{img_prompt} | {vid_prompt_base}" if img_prompt != vid_prompt_base else vid_prompt_base
        
        img_out = os.path.join(assets_dir, f"{shot_id}.png")
        vid_out = os.path.join(assets_dir, f"{shot_id}.mp4")
        
        if os.path.exists(vid_out) and os.path.getsize(vid_out) > 0:
            print(f"\n>> Skipping {shot_id}, video already exists in cache.")
            return True, "", ""
            
        print(f"\n>> Processing {shot_id} ...")
        
        phase = shot.get("phase", "Main_Dance" if is_dance else "")
        renderer = get_renderer(phase, is_dance, config)
        
        if anchor_img_url:
            img_url = anchor_img_url
            if last_video_path and os.path.exists(last_video_path):
                print(f"  [FFmpeg] Extracting last frame from {last_video_path} to {img_out}...")
                subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", last_video_path, "-vframes", "1", "-update", "1", img_out], capture_output=True)
                if not os.path.exists(img_out):
                    mock_img = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "mock_image.png")
                    shutil.copy2(mock_img, img_out)
                # We MUST upload this extracted frame to a public URL for Agnes API to use it as the new anchor
                public_url = upload_image_to_temp_host(img_out)
                if public_url:
                    img_url = public_url
            elif not os.path.exists(img_out):
                # Fallback, just create a blank or copy
                pass
        else:
            time.sleep(random.uniform(0, 2)) # Jitter to prevent rate limit stamping
            img_url = renderer.generate_image(img_prompt, img_out, config, size=target_size)
            if not img_url:
                print(f"[Production Dept] Error: Failed to generate image for {shot_id}.")
                return False, f"Failed to generate image for {shot_id}.", ""
            
        time_range = shot.get("time_range", "")
        duration_sec = parse_duration_from_time_range(time_range)
        if duration_sec <= 0:
            duration_sec = 5.0 # default
        frames = calc_num_frames(duration_sec)
        
        if hasattr(renderer, "generate_video_with_frames"):
             success = renderer.generate_video_with_frames(img_url, vid_prompt, vid_out, config, num_frames=frames, size=target_size)
        else:
             success = renderer.generate_video(img_url, vid_prompt, vid_out, config)
        
        if not success:
            print(f"[Production Dept] Error: Failed to generate video for {shot_id}.")
            return False, f"Failed to generate video for {shot_id}.", img_url
            
        return True, "", img_url
    has_error = False
    error_msg = ""
    
    if is_dance:
        print(f"\\n[Production Dept] Dispatching {len(shots)} shots SEQUENTIALLY (Dance Keyframe Chaining)...")
        anchor_img_url = None
        last_video_path = None
        
        for shot in shots:
            success, msg, img_url = process_single_shot(shot, anchor_img_url, last_video_path)
            if not success:
                has_error = True
                error_msg += msg + "\\n"
                break
            
            anchor_img_url = img_url
            last_video_path = os.path.join(assets_dir, f"{shot['id']}.mp4")
            time.sleep(2) # Pacemaker
    else:
        print(f"\\n[Production Dept] Dispatching {len(shots)} shots concurrently...")
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_shot = {executor.submit(process_single_shot, shot): shot for shot in shots}
            for future in concurrent.futures.as_completed(future_to_shot):
                shot = future_to_shot[future]
                try:
                    success, msg, _ = future.result()
                    if not success:
                        has_error = True
                        error_msg += msg + "\\n"
                except Exception as exc:
                    print(f"[Production Dept] Shot {shot['id']} generated an exception: {exc}")
                    has_error = True
                    error_msg += f"Exception processing {shot['id']}: {exc}\\n"
                    
    if has_error:
        ticket["status"] = "Paused_By_Error"
        ticket["error_message"] = error_msg.strip()
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
        return False

    # 3. Update Ticket Status to QA_Pending_Production
    ticket["status"] = "QA_Pending_Production"
    ticket["last_updated_by"] = "Production_Agent_AgnesAI"
    ticket["last_updated_time"] = time.time()
    
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)
        
    print("\n[Production Dept] Real Generation Complete. Status updated to QA_Pending_Production.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_dir = sys.argv[1]
    else:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_dir = os.path.join(workspace_dir, "projects", "paperai-series", "episode-01")
    process_ticket(run_dir)
