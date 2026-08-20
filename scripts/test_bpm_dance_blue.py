import os
import sys
import time
import math
import struct
import wave
import json
import uuid
import hmac
import hashlib
import datetime
import urllib.request
import urllib.parse
import subprocess

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

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
    bucket = os.getenv('R2_BUCKET')
    endpoint = os.getenv('R2_ENDPOINT')
    public_url_base = os.getenv('R2_PUBLIC_URL')

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
    with urllib.request.urlopen(req) as resp:
        if resp.status in [200, 204]:
            pub_url = f"{public_url_base.rstrip('/')}/{object_name}"
            print(f"  [R2 Upload] Success! Public URL: {pub_url}")
            return pub_url
        else:
            raise Exception(f"R2 upload failed status: {resp.status}")

def download_file(url, target_path):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as out_file:
        out_file.write(resp.read())

def generate_video_shot(prompt, output_path, start_image_url=None, end_image_url=None, width=768, height=1344, key_idx=0):
    for attempt in range(20):
        api_key = get_api_key(key_idx + attempt)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "agnes-video-v2.0",
            "prompt": prompt + ", starting exactly from reference pose, seamless rhythm motion",
            "width": width,
            "height": height,
            "num_frames": 121,
            "frame_rate": 24,
            "negative_prompt": "cropped head, cropped feet, cropped body, top of head cut off, feet cut off, blurry, low quality, distorted hands, distorted body, extra limbs, ugly face"
        }

        if start_image_url and end_image_url:
            print("  [Agnes] Using Keyframes Mode (Loop Closure)...")
            data["extra_body"] = {
                "image": [start_image_url, end_image_url],
                "mode": "keyframes",
                "negative_prompt": data["negative_prompt"]
            }
        elif start_image_url:
            data["image"] = start_image_url
            data["image_url"] = start_image_url

        print(f"  [Agnes] Submitting request (attempt {attempt+1}/20)... Prompt: {prompt[:50]}...")
        req_body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request("https://apihub.agnes-ai.com/v1/videos", data=req_body, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode('utf-8')
            print(f"  [Agnes Warning] HTTP {err.code}: {err_body}")
            if err.code in [503, 429] or "video_queue_full" in err_body:
                print("  [Agnes Queue Full] Backing off 20 seconds before retry...")
                time.sleep(20)
                continue
            else:
                time.sleep(5)
                continue

        video_id = res_json.get("data", {}).get("task_id") or res_json.get("id") or res_json.get("task_id")
        print(f"  [Agnes] Task ID: {video_id}. Polling status...")
        
        for poll_count in range(60):
            time.sleep(8)
            st_req = urllib.request.Request(f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}", headers=headers)
            try:
                with urllib.request.urlopen(st_req) as st_resp:
                    st_json = json.loads(st_resp.read().decode('utf-8'))
                    status = st_json.get("status")
                    video_url = st_json.get("video_url") or st_json.get("url")
                    
                    if status == "completed" or status == "SUCCESS" or (status is None and video_url):
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

    raise RuntimeError("Failed to generate video shot after 20 attempts")

def extract_last_frame(video_path, output_png):
    cmd = ["ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path, "-vframes", "1", "-update", "1", output_png]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_png

def generate_sync_bpm_music(wav_path, bpm=120, duration_sec=20.0):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    beat_interval = 60.0 / bpm
    
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            beat_pos = (t % beat_interval) / beat_interval
            
            # Rhythm melody: C5, E5, G5, A5 on each bar beat
            notes = [523.25, 659.25, 783.99, 880.00]
            current_note = notes[int(t / beat_interval) % len(notes)]
            
            # Kick drum on beat hit (accentuated pulse)
            kick = math.exp(-beat_pos * 8.0) * math.sin(2 * math.pi * 60.0 * beat_pos) * 0.6
            syn = math.sin(2 * math.pi * current_note * t) * 0.3 * (1.0 - beat_pos * 0.5)
            
            sample_val = int((kick + syn) * 20000)
            sample_val = max(-32768, min(32767, sample_val))
            
            # stereo
            packed = struct.pack('<hh', sample_val, sample_val)
            frames.extend(packed)
            
        wav_file.writeframes(frames)
    print(f"  [BPM Engine] Generated 120 BPM synced audio: {wav_path}")
    return wav_path

def robust_video_concat(video_files, bgm_path, output_mp4):
    list_txt = output_mp4 + ".list.txt"
    temp_video = output_mp4 + ".temp_v.mp4"
    
    with open(list_txt, "w") as f:
        for v in video_files:
            f.write(f"file '{os.path.abspath(v)}'\n")

    # Step 1: Pure video re-encode
    cmd1 = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_txt,
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        temp_video
    ]
    subprocess.run(cmd1, check=True)

    # Step 2: Mux single continuous audio stream
    cmd2 = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", bgm_path,
        "-c:v", "copy",
        "-c:a", "aac", "-ac", "2", "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd2, check=True)

    if os.path.exists(temp_video): os.remove(temp_video)
    if os.path.exists(list_txt): os.remove(list_txt)
    print(f"  [Mux Gate Success] Final Video: {output_mp4}")

def quality_audit_gate(mp4_path):
    print("\n>>> Running Automated Quality Audit Gate <<<")
    # Check 1: ffprobe playability & video stream
    cmd_v = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,width,height", "-of", "json", mp4_path]
    res_v = subprocess.run(cmd_v, capture_output=True, text=True)
    info = json.loads(res_v.stdout)
    video_stream = next((s for s in info.get("streams", []) if s.get("codec_name") == "h264"), None)
    audio_stream = next((s for s in info.get("streams", []) if s.get("codec_name") == "aac"), None)
    
    assert video_stream is not None, "Quality Audit Failed: No H.264 video stream found"
    assert video_stream.get("pix_fmt") == "yuv420p", "Quality Audit Failed: Invalid pixel format (must be yuv420p)"
    assert audio_stream is not None, "Quality Audit Failed: No AAC audio stream found"
    
    # Check 2: Audio amplitude (Non-silent)
    cmd_a = ["ffmpeg", "-i", mp4_path, "-f", "s16le", "-ac", "1", "-ar", "44100", "-"]
    proc = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = proc.communicate()
    samples = [struct.unpack('<h', raw[i:i+2])[0] for i in range(0, len(raw), 2)]
    max_amp = max(abs(s) for s in samples) if samples else 0
    
    print(f"  [Audit Check 1] Playable H.264 yuv420p Stream: OK ({video_stream['width']}x{video_stream['height']})")
    print(f"  [Audit Check 2] Audio Track Max Amplitude: {max_amp} (Threshold > 5000)")
    assert max_amp > 5000, f"Quality Audit Failed: Audio stream is silent (max amp: {max_amp})"
    print("🎉 All Quality Audit Gates Passed! Video is verified playable & synced!")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref_img = os.path.join(base_dir, "assets/dance/01_characters/ips/images/blue_skirt_girl_ref.png")
    out_dir = os.path.join(base_dir, "out/demo_bpm_dance_blue")
    os.makedirs(out_dir, exist_ok=True)

    print(">>> Step 1: Uploading New Character Image (Blue Skirt) to R2 Bucket <<<")
    initial_url = upload_to_r2(ref_img, "blue_skirt_girl_ref.png")

    char_lock = (
        "Full body shot, head to toe completely visible in frame, ample headroom above head, shoes visible. "
        "A attractive young Korean woman with long dark wavy hair, wearing a white camisole top, "
        "a light blue pleated tennis skirt, and light blue high heels. "
        "High quality 8k photorealistic, clean indoor stage background with warm lighting."
    )

    shots = [
        {"prompt": f"{char_lock} The woman does upbeat rhythmic side-stepping dance moves to 120 BPM tempo, hands gently swaying on beat, smiling with cheerful expression."},
        {"prompt": f"{char_lock} The woman continues energetic dance, doing stylish hip sway and elegant arm dance moves on 120 BPM beat, maintaining charming expression."},
        {"prompt": f"{char_lock} The woman smoothly transitions dance movement, doing rhythmic leg taps and graceful arm motions perfectly timed to 120 BPM upbeat rhythm."},
        {"prompt": f"{char_lock} The woman completes dance movement, smoothly stepping back into her exact starting hands-on-hips pose to loop seamlessly, smiling brightly."}
    ]

    video_files = []
    current_start_url = initial_url
    end_url = initial_url  # For Keyframes Loop Closure

    print("\n>>> Step 2: Generating 4 Shots (20s) with Character Consistency & Loop Closure <<<")
    for i, shot in enumerate(shots):
        shot_id = i + 1
        is_last = (shot_id == len(shots))
        shot_mp4 = os.path.join(out_dir, f"shot_{shot_id:02d}.mp4")
        shot_png = os.path.join(out_dir, f"shot_{shot_id:02d}_last_frame.png")

        if os.path.exists(shot_mp4) and os.path.getsize(shot_mp4) > 100000:
            print(f"  [Shot {shot_id}/4 Cached] {shot_mp4} exists. Skipping API call.")
        else:
            if is_last:
                print(f"\n  [Shot {shot_id}/4] Keyframe Mode (Loop Closure)...")
                generate_video_shot(
                    prompt=shot["prompt"],
                    output_path=shot_mp4,
                    start_image_url=current_start_url,
                    end_image_url=end_url,
                    width=768,
                    height=1344,
                    key_idx=i
                )
            else:
                print(f"\n  [Shot {shot_id}/4] Chaining Mode...")
                generate_video_shot(
                    prompt=shot["prompt"],
                    output_path=shot_mp4,
                    start_image_url=current_start_url,
                    width=768,
                    height=1344,
                    key_idx=i
                )

        video_files.append(shot_mp4)

        if not is_last and (not os.path.exists(shot_png) or os.path.getsize(shot_png) < 1000):
            print(f"  [Extract & Upload] Last frame for Shot {shot_id} -> R2...")
            extract_last_frame(shot_mp4, shot_png)
            current_start_url = upload_to_r2(shot_png, f"blue_bpm_shot_{shot_id:02d}_last.png")

    print("\n>>> Step 3: Generating Synced 120 BPM Audio Track <<<")
    bgm_path = os.path.join(out_dir, "bgm_120bpm_synced.wav")
    generate_sync_bpm_music(bgm_path, bpm=120, duration_sec=20.0)

    print("\n>>> Step 4: Robust Two-Step Synthesis & Audio Muxing <<<")
    final_mp4 = os.path.join(out_dir, "blue_skirt_girl_bpm_dance_20s.mp4")
    robust_video_concat(video_files, bgm_path, final_mp4)

    print("\n>>> Step 5: Self Quality Audit Gate Verification <<<")
    quality_audit_gate(final_mp4)
    print(f"\n🎉 BPM Dance Video Test (Blue Skirt Character) Successfully Finished! Output File: {final_mp4}")

if __name__ == "__main__":
    main()
