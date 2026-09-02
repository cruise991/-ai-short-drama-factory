#!/usr/bin/env python3
import os
import sys
import time
import uuid
import hmac
import hashlib
import datetime
import argparse
import json
import urllib.request
import urllib.parse
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from character_analyzer import analyze_character_and_scene
from choreography_engine import plan_choreography
from audio_director import prepare_dance_bgm
from video_muxer import robust_video_concat
from quality_auditor import quality_audit_gate

def load_env():
    possible_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), 'ai-short-drama', '.env'),
        '/Users/workspace/ai_short_company/ai-short-drama/.env',
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env')
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ[k.strip()] = v.strip()

load_env()

AGNES_KEYS = [
    os.getenv('AGNES_API_KEY_1'),
    os.getenv('AGNES_API_KEY_2'),
    os.getenv('AGNES_API_KEY_3'),
    os.getenv('AGNES_API_KEY_4'),
    os.getenv('AGNES_API_KEY_5'),
    os.getenv('AGNES_API_KEY_6'),
]
AGNES_KEYS = [k for k in AGNES_KEYS if k]

def get_api_key(idx=0):
    return AGNES_KEYS[idx % len(AGNES_KEYS)] if AGNES_KEYS else os.getenv("AGNES_API_KEY", "")

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing

def upload_to_r2(filepath, object_name=None):
    if not object_name:
        object_name = f"{uuid.uuid4().hex}_{os.path.basename(filepath)}"
    
    access_key = os.getenv('R2_ACCESS_KEY')
    secret_key = os.getenv('R2_SECRET_KEY')
    bucket = os.getenv('R2_BUCKET', 'short-ai')
    endpoint = os.getenv('R2_ENDPOINT')
    public_url_base = os.getenv('R2_PUBLIC_URL')

    if not access_key or not secret_key or not endpoint:
        raise RuntimeError("R2 Cloud Storage credentials missing")

    print(f"  [R2 Upload] Uploading {os.path.basename(filepath)} -> {object_name}...")

    with open(filepath, 'rb') as f:
        content = f.read()

    host = urllib.parse.urlparse(endpoint).netloc
    url = f"{endpoint}/{bucket}/{object_name}"
    
    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    content_type = 'image/jpeg' if filepath.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    payload_hash = hashlib.sha256(content).hexdigest()

    canonical_uri = f"/{bucket}/{object_name}"
    canonical_headers = f"content-type:{content_type}\nhost:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_request = f"PUT\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/auto/s3/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n" + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = get_signature_key(secret_key, date_stamp, "auto", "s3")
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    headers = {
        'Content-Type': content_type,
        'Host': host,
        'x-amz-date': amz_date,
        'x-amz-content-sha256': payload_hash,
        'Authorization': authorization_header
    }

    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=content, headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=45) as resp:
                if resp.status in [200, 204]:
                    pub_url = f"{public_url_base.rstrip('/')}/{object_name}"
                    print(f"  [R2 Upload] Success! Public URL: {pub_url}")
                    return pub_url
                else:
                    raise Exception(f"R2 upload failed status: {resp.status}")
        except Exception as e:
            print(f"  [R2 Upload Warning] Attempt {attempt+1}/5 failed: {e}. Retrying...")
            time.sleep(3)
    raise RuntimeError("Failed to upload to R2 after 5 attempts")

def download_file(url, target_path):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, 'wb') as out_file:
        out_file.write(resp.read())

def generate_video_shot(prompt, output_path, start_image_url=None, end_image_url=None, width=768, height=1344, key_idx=0, is_kneeling_pose=False):
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip('/')
    
    if is_kneeling_pose:
        negative_prompt = (
            "cropped head, head cut off, head out of frame, headless body, missing head, missing face, face cut off, "
            "zoomed-in lower body, torso close-up, bottom half only, lower body only, cropped body, waist-down only, "
            "caucasian face, western features, european face, mature face, sharp masculine jawline, changed face, altered facial identity, non-asian face, "
            "dwarf proportions, stubby legs, average height body, normal proportions, 7-head body ratio, compact build, thick short thighs, short torso, "
            "head turned 180 degrees, backward head, head facing opposite direction of body, neck twist, "
            "head on backwards, exorcist head rotation, broken neck, unnatural spinal twist, chest on back, "
            "back of jacket on front, front clothing on back, torso orientation mismatch, mismatched facing direction, "
            "room change, furniture, sofas, indoor living room, bright room, "
            "blurry, low quality, distorted hands, distorted body, extra limbs, ugly face, disjointed limbs, floating head, floating body"
        )
        prompt_suffix = ", maintaining ultra-tall willowy 9-head supermodel body proportions throughout with legs occupying 55 percent of total body height when standing, graceful fluid anatomical motion, never compressed shortened or squatting, identical clothing and face"
    else:
        negative_prompt = (
            "cropped head, head cut off, head out of frame, headless body, missing head, missing face, face cut off, "
            "zoomed-in lower body, torso close-up, bottom half only, lower body only, cropped body, cropped legs, waist-down only, "
            "caucasian face, western features, european face, mature face, sharp masculine jawline, changed face, altered facial identity, non-asian face, "
            "short legs, compressed height, lowered body, sinking posture, crouching, squatting, bent knees, hunchback, dwarf proportions, stubby legs, average height body, normal proportions, 7-head body ratio, compact build, thick short thighs, short torso, "
            "head turned 180 degrees, backward head, head facing opposite direction of body, neck twist, "
            "head on backwards, exorcist head rotation, broken neck, unnatural spinal twist, chest on back, "
            "back of jacket on front, front clothing on back, torso orientation mismatch, mismatched facing direction, "
            "room change, furniture, sofas, indoor living room, bright room, "
            "cropped feet, feet cut off, blurry, low quality, "
            "distorted hands, distorted body, extra limbs, ugly face, disjointed limbs, floating head, floating body"
        )
        prompt_suffix = ", maintaining ultra-tall willowy 9-head supermodel body proportions throughout with legs occupying at least 55 percent of total body height, fully extended straight long legs at all times, never compressed shortened or squatting, seamless rhythm motion, identical clothing and face"

    for attempt in range(25):
        api_key = get_api_key(key_idx + attempt)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "agnes-video-v2.0",
            "prompt": prompt + prompt_suffix,
            "width": width,
            "height": height,
            "num_frames": 121,
            "frame_rate": 24,
            "negative_prompt": negative_prompt
        }

        if start_image_url and end_image_url:
            print("  [Agnes API] Mode: Keyframes (Loop Closure)...")
            data["extra_body"] = {
                "image": [start_image_url, end_image_url],
                "mode": "keyframes",
                "negative_prompt": negative_prompt
            }
        elif start_image_url:
            data["image"] = start_image_url
            data["image_url"] = start_image_url

        print(f"  [Agnes API] Submitting request (attempt {attempt+1}/25)... Prompt: {prompt[:60]}...")
        req_body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/videos", data=req_body, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode('utf-8')
            print(f"  [Agnes Warning] HTTP {err.code}: {err_body}")
            time.sleep(8)
            continue
        except Exception as e:
            print(f"  [Agnes Network Warning] {e}")
            time.sleep(8)
            continue

        video_id = res_json.get("data", {}).get("task_id") or res_json.get("id") or res_json.get("task_id")
        print(f"  [Agnes API] Task ID: {video_id}. Polling status...")
        
        poll_endpoints = [
            f"{base_url}/videos/{video_id}",
            f"{base_url.replace('/v1', '')}/agnesapi?video_id={video_id}"
        ]
        
        for poll_count in range(80):
            time.sleep(6)
            for ep in poll_endpoints:
                try:
                    st_req = urllib.request.Request(ep, headers=headers)
                    with urllib.request.urlopen(st_req, timeout=30) as st_resp:
                        st_json = json.loads(st_resp.read().decode('utf-8'))
                        status = st_json.get("status") or st_json.get("internal_status")
                        video_url = st_json.get("video_url") or st_json.get("url")
                        
                        if status in ["completed", "SUCCESS"] or (video_url and status not in ["failed", "FAILED", "processing", "pending", "in_progress"]):
                            print(f"  [Agnes Success] Video URL: {video_url}")
                            download_file(video_url, output_path)
                            print(f"  [Downloaded] -> {output_path}")
                            return output_path
                        elif status in ["FAILED", "failed"]:
                            print(f"  [Agnes Failed] {st_json}")
                            break
                        else:
                            if poll_count % 2 == 0 and ep == poll_endpoints[0]:
                                print(f"  [Agnes Polling] Waiting for task {video_id}... status={status}")
                            break
                except urllib.error.HTTPError as he:
                    if he.code == 404:
                        continue
                    print(f"  [Agnes Poll Warning] HTTP {he.code}: {he}")
                except Exception as e:
                    print(f"  [Agnes Poll Warning] {e}")

    raise RuntimeError("Failed to generate video shot after multiple attempts")

def extract_last_frame_lossless(video_path, output_png):
    cmd = [
        "ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path,
        "-vf", "unsharp=3:3:0.5:3:3:0.0",
        "-pix_fmt", "rgb24",
        "-vframes", "1", "-update", "1", output_png
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_png


def check_body_proportion(frame_png, min_body_ratio=0.72):
    """Lightweight check: estimate if character fills enough vertical space.
    Returns True if proportion looks acceptable, False if body appears compressed."""
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=height",
               "-of", "csv=p=0", frame_png]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        frame_h = int(result.stdout.strip())
        cmd2 = ["ffmpeg", "-y", "-i", frame_png,
                "-vf", "format=gray,crop=iw/3:ih:iw/3:0",
                "-f", "rawvideo", "-pix_fmt", "gray", "-"]
        proc = subprocess.run(cmd2, capture_output=True, timeout=10)
        raw = proc.stdout
        if not raw:
            return True
        w = len(raw) // frame_h if frame_h > 0 else 1
        if w <= 0:
            return True
        row_avgs = []
        for y in range(frame_h):
            row_start = y * w
            row_data = raw[row_start:row_start + w]
            if row_data:
                row_avgs.append(sum(row_data) / len(row_data))
            else:
                row_avgs.append(255)
        if not row_avgs:
            return True
        bg_top = sum(row_avgs[:5]) / 5
        bg_bot = sum(row_avgs[-5:]) / 5
        bg_ref = (bg_top + bg_bot) / 2
        threshold = 30
        top_body = 0
        bot_body = frame_h - 1
        for y in range(frame_h):
            if abs(row_avgs[y] - bg_ref) > threshold:
                top_body = y
                break
        for y in range(frame_h - 1, -1, -1):
            if abs(row_avgs[y] - bg_ref) > threshold:
                bot_body = y
                break
        body_h = bot_body - top_body
        ratio = body_h / frame_h if frame_h > 0 else 1.0
        print(f"  [Proportion Check] Body occupies {ratio:.1%} of frame (threshold: {min_body_ratio:.0%})")
        return ratio >= min_body_ratio
    except Exception as e:
        print(f"  [Proportion Check] Skipped due to error: {e}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Character Consistent Dance Skill Pipeline Pro")
    parser.add_argument("--input-image", required=True, help="Path to character reference image")
    parser.add_argument("--duration", type=int, default=30, help="Total video duration in seconds (15, 20, 25, 30, 40)")
    parser.add_argument("--template", default=None, help="Dance template ID or name from assets/dance/07_templates (e.g. DANCE_THAI_SWAY)")
    parser.add_argument("--style", default="street", choices=["fitness", "kpop", "street", "luxury"], help="Dance style archetype")
    parser.add_argument("--prompt-desc", default=None, help="Optional custom character/scene description override")
    parser.add_argument("--bpm", type=int, default=115, help="Music tempo in BPM")
    parser.add_argument("--bgm", default=None, help="Optional path to custom BGM audio file or preset")
    parser.add_argument("--output", required=True, help="Path for final audited output MP4 video")
    args = parser.parse_args()

    num_shots = max(1, args.duration // 5)
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n========================================================")
    print(f"🚀 Character Dance Skill Pipeline Pro ({args.duration}s, {num_shots} Shots, Style: {args.style.upper()}, BPM: {args.bpm})")
    if args.template:
        print(f"🎯 Template Mode: {args.template}")
    print(f"========================================================\n")

    print(">>> Step 1: Character & Scene Feature Analysis <<<")
    char_meta = analyze_character_and_scene(args.input_image, user_desc=args.prompt_desc, style_hint=args.style)
    char_lock_prompt = char_meta["full_prompt_lock"]
    print(f"  [Prompt Lock]: {char_lock_prompt}")

    print("\n>>> Step 2: Uploading Reference Image -> Cloud R2 Bucket <<<")
    initial_url = upload_to_r2(args.input_image)

    print("\n>>> Step 3: Planning Professional Choreography <<<")
    is_kneeling = char_meta.get("is_kneeling_pose", False)
    shots = plan_choreography(style=args.style, duration=args.duration, bpm=args.bpm, char_lock_prompt=char_lock_prompt, template_id=args.template, is_rear_pose=char_meta.get("is_rear_pose", False), is_kneeling_pose=is_kneeling)

    video_files = []
    current_start_url = initial_url
    end_url = initial_url

    print(f"\n>>> Step 4: Generating {num_shots} Shots with Chaining & Loop Closure <<<")
    for i, shot in enumerate(shots):
        shot_id = shot["shot_id"]
        is_last = shot["is_loop_closure"]
        shot_mp4 = os.path.join(out_dir, f"skill_shot_{shot_id:02d}.mp4")
        shot_png = os.path.join(out_dir, f"skill_shot_{shot_id:02d}_last_frame.png")

        if os.path.exists(shot_mp4) and os.path.getsize(shot_mp4) > 200000:
            print(f"\n  [Shot {shot_id}/{num_shots}] Found existing valid shot -> {shot_mp4} (Skipping API call)")
        else:
            if is_last:
                print(f"\n  [Shot {shot_id}/{num_shots}] Keyframes Loop Closure Mode...")
                generate_video_shot(shot["prompt"], shot_mp4, current_start_url, end_url, key_idx=i, is_kneeling_pose=is_kneeling)
            else:
                print(f"\n  [Shot {shot_id}/{num_shots}] Chaining Mode...")
                generate_video_shot(shot["prompt"], shot_mp4, current_start_url, key_idx=i, is_kneeling_pose=is_kneeling)

        video_files.append(shot_mp4)

        if not is_last:
            if not (os.path.exists(shot_png) and os.path.getsize(shot_png) > 50000):
                print(f"  [Extract & Upload] Shot {shot_id} last frame (Lossless + Unsharp) -> R2...")
                extract_last_frame_lossless(shot_mp4, shot_png)
                # Fix E: Per-shot body proportion quality check
                if not check_body_proportion(shot_png):
                    print(f"  [Proportion Warning] Shot {shot_id} body appears compressed - proportion below threshold")
            else:
                print(f"  [Resume] Using existing Shot {shot_id} last frame -> {shot_png}")
            current_start_url = upload_to_r2(shot_png, f"{args.style}_shot_{shot_id:02d}_last.png")

    print("\n>>> Step 5: Audio Director Preparing Master BGM Track <<<")
    bgm_path = os.path.join(out_dir, f"master_bgm_{args.duration}s.wav")
    prepare_dance_bgm(bgm_path, duration_sec=float(args.duration), style=args.style, template_id=args.template, custom_bgm=args.bgm, bpm=args.bpm)

    print("\n>>> Step 6: Safe Two-Step Muxing & Encoding <<<")
    robust_video_concat(video_files, bgm_path, args.output)

    print("\n>>> Step 7: Tri-Tier Quality Audit Gate Assertion <<<")
    quality_audit_gate(args.output)
    print(f"🎉 Skill Execution Completed! Output File: {args.output}\n")

if __name__ == "__main__":
    main()
