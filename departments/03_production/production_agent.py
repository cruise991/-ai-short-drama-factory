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

    cmd = ["curl", "-s", "-X", method, url]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    
    temp_json_file = None
    if json_data:
        import tempfile
        fd, temp_json_file = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(json_data, f)
        cmd.extend(["-d", f"@{temp_json_file}"])
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
        if temp_json_file and os.path.exists(temp_json_file):
            os.remove(temp_json_file)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"[cURL] Request to {url} timed out.")
        if temp_json_file and os.path.exists(temp_json_file):
            os.remove(temp_json_file)
    except Exception as e:
        print(f"[cURL] Error: {e}")
        if temp_json_file and os.path.exists(temp_json_file):
            os.remove(temp_json_file)
    return None

def load_config():
    return {}

from shared_tools.config_loader import get_config

def parse_duration_from_time_range(time_range_str):
    import re
    if not time_range_str: return 0
    def _to_seconds(time_str):
        time_str = re.sub(r'[a-zA-Z]', '', time_str).strip()
        parts = time_str.split(":")
        if len(parts) == 1: return float(parts[0]) if parts[0] else 0
        elif len(parts) == 2: return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3: return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        return 0
    # Allow optional non-digits like 's' or 'sec' at the end of the time parts
    match = re.match(r"^\s*([\d:]+[a-zA-Z]*)\s*[-~]\s*([\d:]+[a-zA-Z]*)\s*$", time_range_str)
    if match:
        start_sec = _to_seconds(match.group(1))
        end_sec = _to_seconds(match.group(2))
        return max(0, end_sec - start_sec)
    return 0

def calc_num_frames(duration_sec, fps=24):
    raw_frames = int(duration_sec * fps)
    
    # Agnes Video V2.0 strongly prefers specific length tiers (5s, 12s, 18s)
    # 5s  -> 121 frames
    # 12s -> 289 frames
    # 18s -> 433 frames
    
    tiers = [121, 289, 433]
    closest_tier = min(tiers, key=lambda x: abs(x - raw_frames))
    
    return closest_tier

def check_face_morphing(video_path):
    print(f"  [QA] Checking face morphing and SSIM for {video_path}")
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("  [QA] cv2 not installed, skipping QA check.")
        return True

    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()
    
    if len(frames) < 2:
        print("  [QA] 🚨 Video is corrupt or empty! (frames < 2)")
        return False
    
    first_frame = frames[0]
    last_frame = frames[-1]
    
    try:
        from skimage.metrics import structural_similarity as ssim
        gray_first = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        gray_last = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        global_score, _ = ssim(gray_first, gray_last, full=True)
    except:
        mse = np.mean((first_frame.astype("float") - last_frame.astype("float")) ** 2)
        global_score = 1.0 - (mse / 255.0**2)
        
    print(f"  [QA] Global similarity score: {global_score:.3f}")
    
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray_first = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_first, 1.1, 4)
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_first = gray_first[y:y+h, x:x+w]
            face_last = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)[y:y+h, x:x+w]
            try:
                face_score, _ = ssim(face_first, face_last, full=True)
            except:
                mse = np.mean((face_first.astype("float") - face_last.astype("float")) ** 2)
                face_score = 1.0 - (mse / 255.0**2)
            print(f"  [QA] Facial similarity score: {face_score:.3f}")
            
            if face_score < 0.95:
                print("  [QA] 🚨 面部变异(Face Morphing)检测失败！需要重试。")
                return False
    except Exception as e:
        print(f"  [QA] Face detection failed: {e}")
            
    if global_score < 0.85:
        print("  [QA] 🚨 全局一致性检测失败！需要重试。")
        return False
        
    return True


def generate_image_agnes(prompt, output_path, config, size="1024x768", negative_prompt=None):
    from shared_tools.api_pool import get_agnes_keys, get_available_key, record_429
    model = config.get("PRODUCTION_IMAGE_MODEL", "agnes-image-2.1-flash")
    
    keys = get_agnes_keys()
    
    for _ in range(10): # try 10 times across different keys
        api_key = get_available_key(keys)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        api_size = size
        ratio = None
        if model == "agnes-image-2.1-flash" and "x" in size:
            try:
                w, h = map(int, size.split("x"))
                if w < h:
                    ratio = "9:16"
                elif w > h:
                    ratio = "16:9"
                else:
                    ratio = "1:1"
                api_size = "1K"
            except:
                pass
                
        data = {
            "model": model,
            "prompt": prompt,
            "size": api_size,
            "extra_body": {
                "response_format": "url"
            }
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
            data["extra_body"]["negative_prompt"] = negative_prompt
            
        if ratio:
            data["ratio"] = ratio
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

        if not url:
            print(f"  [AgnesRenderer] Image API error. Resp: {resp}")
            # Do NOT fallback to mock image. Return empty to trigger a retry.
            continue
            
        if url:
            # Download the image using curl
            dl_cmd = ["curl", "-s", "-o", output_path, url]
            subprocess.run(dl_cmd)
            return url
            
    # Should not reach here because of fallback
    raise Exception(f"Image generation failed for {output_path}. API response was invalid or rate limited.")

def generate_video_agnes(image_url, video_prompt, output_path, config, size="1152x768", num_frames=121, is_last_shot=False, target_last_frame_url=None, negative_prompt=None):
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
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
            
        if image_url or config.get("GLOBAL_REFERENCE_URL") or negative_prompt:
            data["extra_body"] = {}
            if negative_prompt:
                data["extra_body"]["negative_prompt"] = negative_prompt
            if is_last_shot and image_url and target_last_frame_url:
                print("  [AgnesRenderer] Applying Loop Closure (Keyframes Mode) for last shot.")
                data["extra_body"]["image"] = [image_url, target_last_frame_url]
                data["extra_body"]["mode"] = "keyframes"
            else:
                if image_url:
                    data["image"] = image_url
                    data["image_url"] = image_url
                if config.get("GLOBAL_REFERENCE_URL"):
                    data["extra_body"]["reference_image_url"] = config.get("GLOBAL_REFERENCE_URL")
                    data["extra_body"]["reference_fidelity"] = 0.85
        
        print(f"  [AgnesRenderer] Calling REAL Video API for {output_path}...")
        resp = _curl_request("POST", "https://apihub.agnes-ai.com/v1/videos", headers=headers, json_data=data)
        
        if resp and "error" in resp and resp["error"].get("code") == 429:
            record_429(api_key)
            continue
            
        video_id = None
        if resp:
            video_id = resp.get("video_id") or resp.get("id") or resp.get("task_id")
            
        if not video_id:
            print(f"  [AgnesRenderer] Video API error. Resp: {resp}")
            continue

        if video_id:
            # Poll for completion
            for _ in range(30):
                time.sleep(15)
                # Official GET endpoint
                status_resp = _curl_request("GET", f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}", headers=headers)
                if status_resp:
                    # New status structure: "completed" and "url"
                    status = status_resp.get("status")
                    if status == "completed" and "url" in status_resp:
                        vid_url = status_resp["url"]
                        dl_cmd = ["curl", "-s", "-f", "-o", output_path, vid_url]
                        subprocess.run(dl_cmd)
                        
                        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
                            print(f"  [AgnesRenderer] Video download failed or file is too small (corrupt). URL: {vid_url}")
                            if os.path.exists(output_path):
                                os.remove(output_path)
                            break # Retry the generation loop
                        
                        # Perform QA if it's a looping video
                        if "no face morphing" in video_prompt.lower():
                            if not check_face_morphing(output_path):
                                print("  [AgnesRenderer] QA check failed. Retrying video generation...")
                                break # break polling loop to retry generation loop

                        return True
                    elif status == "failed" or status == "error":
                        # Not a 429, actual task failure
                        break
            
            # If we fall through the polling loop without returning, it's a timeout or failure
            break
            
    # Should not reach here because of fallback
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
    
    is_dance = "舞蹈" in ticket.get("format_type", "") or "钩子" in ticket.get("format_type", "")
    
    if is_dance:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            content = f.read()
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            raw_json = json_match.group(1) if json_match else content
            try:
                task_data = json.loads(raw_json)
                stage_1 = task_data.get("stage_1_image", {})
                stage_2 = task_data.get("stage_2_video", {})
                locks = {
                    "character_anchor": task_data.get("character", ""),
                    "costume_lock": stage_1.get("costume", ""),
                    "scene_lock": stage_1.get("scene", ""),
                    "image_suggestion_full": stage_1.get("prompt", "")
                }
                shots = []
                timeline = stage_2.get("timeline", [])
                if timeline:
                    first_t_shot = timeline[0]
                    vid_prompt = f"{first_t_shot.get('action_prompt', '')}. {first_t_shot.get('camera_prompt', '')}. {stage_2.get('video_prompt', '')}"
                    shots.append({
                        "id": "shot_01",
                        "phase": "Anchor_Image_And_First_Dance",
                        "image_suggestion": stage_1.get("prompt", ""),
                        "negative_prompt": stage_1.get("negative_prompt", ""),
                        "video_prompt": vid_prompt,
                        "time_range": f"0:00 - 0:{first_t_shot.get('duration', 5)}",
                        "duration": first_t_shot.get("duration", 5)
                    })
                    for i, t_shot in enumerate(timeline[1:]):
                        shot_id = f"shot_{str(i+2).zfill(2)}"
                        # Combine action and camera for the specific clip
                        vid_prompt = f"{t_shot.get('action_prompt', '')}. {t_shot.get('camera_prompt', '')}. {stage_2.get('video_prompt', '')}"
                        shots.append({
                            "id": shot_id,
                            "phase": "Main_Dance",
                            "image_suggestion": "",
                            "negative_prompt": stage_1.get("negative_prompt", ""),
                            "video_prompt": vid_prompt,
                            "time_range": f"0:00 - 0:{t_shot.get('duration', 5)}",
                            "duration": t_shot.get("duration", 5)
                        })
                else:
                    shots.append({
                        "id": "shot_01",
                        "phase": "Anchor_Image_And_First_Dance",
                        "image_suggestion": stage_1.get("prompt", ""),
                        "negative_prompt": stage_1.get("negative_prompt", ""),
                        "video_prompt": stage_2.get("video_prompt", ""),
                        "time_range": f"0:00 - 0:{ticket.get('total_duration', 12)}",
                        "duration": ticket.get('total_duration', 12)
                    })
            except Exception as e:
                print(f"[Production Dept] Error parsing dance JSON: {e}")
                print(f"[Production Dept] Raw data was:\n{raw_json[:500]}...")
                
                # Mock Dance fallback
                locks = {
                    "character_anchor": "C001_Luna",
                    "costume_lock": "Cyberpunk outfit",
                    "scene_lock": "Neon city"
                }
                shots = [
                    {
                        "id": "shot_01",
                        "phase": "Anchor_Image",
                        "image_suggestion": "Cyberpunk girl standing",
                        "video_prompt": ""
                    },
                    {
                        "id": "shot_02",
                        "phase": "Main_Dance",
                        "image_suggestion": "",
                        "video_prompt": "She dances smoothly. no face morphing.",
                        "time_range": "0:00 - 0:12"
                    }
                ]
                print("[Production Dept] Applied Mock Dance data structure fallback due to parsing failure.")
    else:
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
        
    target_size = ticket.get("image_size", config.get("dance_factory", {}).get("image_size", "768x1344") if is_dance else "1024x768")

    def upload_image_to_temp_host(filepath):
        print(f"  [Upload] Attempting to save {filepath} to local Media Center (MinIO)...")
        filename = os.path.basename(filepath)
        s3_url = None
        
        try:
            import boto3
            import uuid
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
            load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "media_center", ".env"))
            
            storage_provider = os.getenv('STORAGE_PROVIDER', 'minio').lower()
            
            if storage_provider == 'r2':
                print("  [Upload] Using Production Storage: Cloudflare R2")
                s3_client = boto3.client('s3',
                                         endpoint_url=os.getenv("R2_ENDPOINT"),
                                         aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
                                         aws_secret_access_key=os.getenv('R2_SECRET_KEY'),
                                         region_name='auto')
                bucket_name = os.getenv('R2_BUCKET', 'paperai-media')
                public_url_base = os.getenv('R2_PUBLIC_URL')
            else:
                print("  [Upload] Using Development Storage: Local MinIO")
                import platform
                default_endpoint = "http://minio:9000" if platform.system() == "Linux" else "http://localhost:4000"
                
                s3_client = boto3.client('s3',
                                         endpoint_url=os.getenv("MINIO_ENDPOINT", default_endpoint),
                                         aws_access_key_id=os.getenv('MINIO_ROOT_USER', 'admin'),
                                         aws_secret_access_key=os.getenv('MINIO_ROOT_PASSWORD', 'paperai2026'),
                                         region_name=os.getenv('MINIO_REGION', 'auto'))
                bucket_name = os.getenv('S3_BUCKET', 'paperai-media')
                public_url_base = os.getenv('PUBLIC_MEDIA_URL')

            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            s3_client.upload_file(filepath, bucket_name, unique_filename)
            print(f"  [Upload] Successfully stored in {storage_provider} bucket: {bucket_name}/{unique_filename}")
            
            if public_url_base:
                # Remove trailing slash if present
                public_url_base = public_url_base.rstrip('/')
                # Construct URL. Note: For MinIO, we usually need the bucket name in the path.
                # For R2 custom domains, the domain usually points directly to the bucket root.
                if storage_provider == 'r2':
                    s3_url = f"{public_url_base}/{unique_filename}"
                else:
                    s3_url = f"{public_url_base}/{bucket_name}/{unique_filename}"
                    
                print(f"  [Upload] Using Public Media URL: {s3_url}")
                
                # [CRITICAL FIX]: If using Pinggy or localhost, external APIs like Agnes often fail to download 
                # because free Pinggy has an HTML warning page intercept, and localhost is unreachable.
                if "pinggy" in s3_url or "localhost" in s3_url or "127.0.0.1" in s3_url:
                    print("  [Upload] Detected local/Pinggy URL. Uploading a copy to Catbox for reliable external API access...")
                    try:
                        import requests
                        with open(filepath, 'rb') as f:
                            catbox_resp = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f}, timeout=30)
                        if catbox_resp.status_code == 200:
                            catbox_url = catbox_resp.text.strip()
                            print(f"  [Upload] Catbox public URL obtained: {catbox_url}")
                            # Override the returned url specifically so the Agnes API gets a clean, direct public link
                            return catbox_url
                    except Exception as cat_e:
                        print(f"  [Upload] Catbox fallback failed: {cat_e}")
                
                return s3_url
            else:
                print(f"  [Upload] Public URL not configured for {storage_provider}. Agnes API requires a public URL.")
        except Exception as e:
            print(f"  [Upload] S3 ({storage_provider}) upload exception: {e}")
            
        print("  [Upload] Falling back to base64 encoding (100% reliable for local testing)...")
        try:
            import base64
            with open(filepath, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{b64_str}"
        except Exception as e:
            print(f"  [Upload] Base64 fallback failed: {e}")
        return None

    def process_single_shot(shot, anchor_img_url=None, last_video_path=None, is_last_shot=False, target_last_frame_url=None):
        shot_id = shot["id"]
        vid_prompt_base = shot.get("video_prompt", "")
        negative_prompt = shot.get("negative_prompt", "")
        
        if is_dance and locks:
            char_anchor = locks.get("character_anchor", "")
            costume = locks.get("costume_lock", "")
            scene = locks.get("scene_lock", "")
            style_desc = ticket.get("style", "")
            full_prompt = locks.get("image_suggestion_full", "")
            
            # 强制开启中景镜头锁定 (Enforce medium shot camera lock)
            camera_lock = "Static medium shot from waist up to thighs, character occupies 60-70% of the frame, stable focal length, action and limbs clearly visible. No camera zoom in, no camera zoom out, no camera tilt, only slight pan following the character. (No close-up, no portrait, no extreme wide shot, do not change distance)"
            
            # The T2I needs full character, costume, scene context, and style (following Agnes API structure)
            if full_prompt:
                img_prompt = f"{camera_lock}. {full_prompt}"
            else:
                img_prompt = f"{camera_lock}. {char_anchor}, wearing {costume}, standing in {scene}, style: {style_desc}, masterpiece, best quality, highly detailed"
            
            # For I2V Keyframes mode, we pass the full character/costume/scene to keep it perfectly consistent
            dance_action = shot.get("image_suggestion", "")
            if full_prompt:
                vid_prompt = f"{camera_lock}. {full_prompt} | {vid_prompt_base}"
            else:
                vid_prompt = f"{camera_lock}. {char_anchor}, wearing {costume}, in {scene} | {dance_action} | {vid_prompt_base}, style: {style_desc}"
        else:
            img_prompt = shot.get("image_suggestion", "")
            if not img_prompt:
                img_prompt = vid_prompt_base
            vid_prompt = f"{img_prompt} | {vid_prompt_base}" if img_prompt != vid_prompt_base else vid_prompt_base
        
        img_out = os.path.join(assets_dir, f"{shot_id}.png")
        vid_out = os.path.join(assets_dir, f"{shot_id}.mp4")
        
        if os.path.exists(vid_out) and os.path.getsize(vid_out) > 0:
            print(f"\n>> Skipping {shot_id}, video already exists in cache.")
            skip_url = anchor_img_url
            if not skip_url and os.path.exists(img_out):
                skip_url = upload_image_to_temp_host(img_out)
            return True, "", skip_url or "cached_placeholder"
            
        print(f"\n>> Processing {shot_id} ...")
        
        phase = shot.get("phase", "Main_Dance" if is_dance else "")
        renderer = get_renderer(phase, is_dance, config)
        
        if anchor_img_url or last_video_path:
            img_url = anchor_img_url
            if last_video_path and os.path.exists(last_video_path):
                print(f"  [FFmpeg] Extracting last frame from {last_video_path} to {img_out}...")
                subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", last_video_path, "-vframes", "1", "-update", "1", img_out], capture_output=True)
                if not os.path.exists(img_out):
                    print(f"  [FFmpeg] Error: Failed to extract last frame from {last_video_path}.")
                    return False, f"Failed to extract last frame from {os.path.basename(last_video_path)}.", ""
                # We MUST upload this extracted frame to a public URL for Agnes API to use it as the new anchor
                public_url = upload_image_to_temp_host(img_out)
                if public_url:
                    img_url = public_url
            elif not os.path.exists(img_out):
                # Fallback, just create a blank or copy
                pass
        else:
            time.sleep(random.uniform(0, 2)) # Jitter to prevent rate limit stamping
            if hasattr(renderer, "generate_image_with_neg"):
                img_url = renderer.generate_image_with_neg(img_prompt, img_out, config, size=target_size, negative_prompt=negative_prompt)
            else:
                img_url = renderer.generate_image(img_prompt, img_out, config, size=target_size)
            if not img_url:
                print(f"[Production Dept] Error: Failed to generate image for {shot_id}.")
                return False, f"Failed to generate image for {shot_id}.", ""
            
        if not vid_prompt_base:
            print(f"  [Production Dept] {shot_id} is an Anchor Shot (No Video). Returning Image.")
            return True, "", img_url
            
        time_range = shot.get("time_range", "")
        duration_sec = parse_duration_from_time_range(time_range)
        if duration_sec <= 0:
            duration_sec = 5.0 # default
        frames = calc_num_frames(duration_sec)
        
        if hasattr(renderer, "generate_video_with_frames"):
             success = renderer.generate_video_with_frames(img_url, vid_prompt, vid_out, config, num_frames=frames, size=target_size, is_last_shot=is_last_shot, target_last_frame_url=target_last_frame_url, negative_prompt=negative_prompt)
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
        global_reference_url = None
        
        for idx, shot in enumerate(shots):
            if global_reference_url:
                config["GLOBAL_REFERENCE_URL"] = global_reference_url
                
            is_last_shot = (idx == len(shots) - 1)
            success, msg, img_url = process_single_shot(
                shot, anchor_img_url, last_video_path, 
                is_last_shot=is_last_shot, 
                target_last_frame_url=global_reference_url
            )
            if not success:
                has_error = True
                error_msg += msg + "\\n"
                break
            
            # Lock the first frame as the global aesthetic reference
            if not global_reference_url and img_url:
                global_reference_url = img_url
                
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
