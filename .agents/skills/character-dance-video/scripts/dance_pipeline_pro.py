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

    req = urllib.request.Request(url, data=content, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status in [200, 204]:
            pub_url = f"{public_url_base.rstrip('/')}/{object_name}"
            print(f"  [R2 Upload] Success! Public URL: {pub_url}")
            return pub_url
        else:
            raise Exception(f"R2 upload failed status: {resp.status}")

def download_file(url, target_path):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, 'wb') as out_file:
        out_file.write(resp.read())

def generate_video_shot(prompt, output_path, start_image_url=None, end_image_url=None, width=768, height=1344, key_idx=0):
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip('/')
    
    negative_prompt = (
        "plaid, large checkered pattern, large squares, windowpane check, thick lines, "
        "belt, waistband, waist tie, bow, ribbon, drawstring, rope, belt buckle, elastic band on waist, "
        "two-piece top, separated skirt, apron look, skirt length change, long dress, maxi dress, "
        "crouching, squatting, bent knees, hunchback, short legs, compressed height, lowered body, sinking posture, "
        "western face, caucasian, mature face, sharp jawline, facial features change, "
        "room change, furniture, sofas, indoor living room, bright room, "
        "cropped head, cropped feet, cropped body, top of head cut off, feet cut off, blurry, low quality, "
        "distorted hands, distorted body, extra limbs, ugly face"
    )

    for attempt in range(25):
        api_key = get_api_key(key_idx + attempt)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "agnes-video-v2.0",
            "prompt": prompt + ", standing ultra tall with long straight legs, seamless rhythm motion, identical clothing and face",
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
        
        for poll_count in range(60):
            time.sleep(8)
            st_req = urllib.request.Request(f"{base_url.replace('/v1', '')}/agnesapi?video_id={video_id}", headers=headers)
            try:
                with urllib.request.urlopen(st_req, timeout=30) as st_resp:
                    st_json = json.loads(st_resp.read().decode('utf-8'))
                    status = st_json.get("status")
                    video_url = st_json.get("video_url") or st_json.get("url")
                    
                    if status in ["completed", "SUCCESS"] or (status is None and video_url):
                        print(f"  [Agnes Success] Video URL: {video_url}")
                        download_file(video_url, output_path)
                        print(f"  [Downloaded] -> {output_path}")
                        return output_path
                    elif status in ["FAILED", "failed"]:
                        print(f"  [Agnes Failed] {st_json}")
                        break
                    else:
                        if poll_count % 2 == 0:
                            print(f"  [Agnes Polling] Waiting for task {video_id}... status={status}")
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
    shots = plan_choreography(style=args.style, duration=args.duration, bpm=args.bpm, char_lock_prompt=char_lock_prompt, template_id=args.template)

    video_files = []
    current_start_url = initial_url
    end_url = initial_url

    print(f"\n>>> Step 4: Generating {num_shots} Shots with Chaining & Loop Closure <<<")
    for i, shot in enumerate(shots):
        shot_id = shot["shot_id"]
        is_last = shot["is_loop_closure"]
        shot_mp4 = os.path.join(out_dir, f"skill_shot_{shot_id:02d}.mp4")
        shot_png = os.path.join(out_dir, f"skill_shot_{shot_id:02d}_last_frame.png")

        if is_last:
            print(f"\n  [Shot {shot_id}/{num_shots}] Keyframes Loop Closure Mode...")
            generate_video_shot(shot["prompt"], shot_mp4, current_start_url, end_url, key_idx=i)
        else:
            print(f"\n  [Shot {shot_id}/{num_shots}] Chaining Mode...")
            generate_video_shot(shot["prompt"], shot_mp4, current_start_url, key_idx=i)

        video_files.append(shot_mp4)

        if not is_last:
            print(f"  [Extract & Upload] Shot {shot_id} last frame (Lossless + Unsharp) -> R2...")
            extract_last_frame_lossless(shot_mp4, shot_png)
            current_start_url = upload_to_r2(shot_png, f"{args.style}_shot_{shot_id:02d}_last.png")

    print("\n>>> Step 5: Audio Director Preparing Master BGM Track <<<")
    bgm_path = os.path.join(out_dir, f"master_bgm_{args.duration}s.wav")
    prepare_dance_bgm(bgm_path, duration_sec=float(args.duration), style=args.style, custom_bgm=args.bgm, bpm=args.bpm)

    print("\n>>> Step 6: Safe Two-Step Muxing & Encoding <<<")
    robust_video_concat(video_files, bgm_path, args.output)

    print("\n>>> Step 7: Tri-Tier Quality Audit Gate Assertion <<<")
    quality_audit_gate(args.output)
    print(f"🎉 Skill Execution Completed! Output File: {args.output}\n")

if __name__ == "__main__":
    main()
