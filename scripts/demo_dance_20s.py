import os
import sys
import time
import json
import uuid
import hmac
import hashlib
import datetime
import urllib.request
import urllib.parse
import urllib.error
import subprocess

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

    print(f"  [R2 Upload] Uploading {os.path.basename(filepath)} -> bucket {bucket}/{object_name}...")

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

def generate_video_shot(prompt, output_path, start_image_url=None, end_image_url=None, width=768, height=1344):
    for attempt in range(20):
        api_key = get_api_key(attempt)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "agnes-video-v2.0",
            "prompt": prompt + ", starting exactly from the reference pose, seamless continuation",
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

        print(f"  [Agnes] Submitting request (attempt {attempt+1}/20)...")
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
            raise Exception(f"Agnes API error {err.code}: {err_body}")

        print(f"  [Agnes] Task submitted: {res_json}")
        video_id = res_json.get("video_id") or res_json.get("id") or res_json.get("task_id")
        if not video_id:
            print("  [Agnes] Task ID missing, retrying...")
            time.sleep(10)
            continue

        print(f"  [Agnes] Polling status for task {video_id}...")
        for poll in range(120):
            time.sleep(15)
            st_req = urllib.request.Request(f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}", headers=headers)
            try:
                with urllib.request.urlopen(st_req) as st_resp:
                    st_json = json.loads(st_resp.read().decode('utf-8'))
            except Exception as e:
                print(f"    Polling [{poll+1}/120] Exception: {e}")
                continue

            status = st_json.get("status") or st_json.get("state")
            print(f"    Polling [{poll+1}/120] Status: {status}")

            if status in ["completed", "succeeded", "success", "FINISH"]:
                vid_url = st_json.get("video_url") or st_json.get("url")
                if not vid_url and isinstance(st_json.get("result"), dict):
                    vid_url = st_json["result"].get("url")
                if not vid_url and isinstance(st_json.get("data"), dict):
                    vid_url = st_json["data"].get("url")
                if not vid_url and "output" in st_json:
                    vid_url = st_json["output"].get("video_url")
                
                if not vid_url:
                    for k in ["video", "download_url", "file_url"]:
                        if k in st_json:
                            vid_url = st_json[k]
                            break

                if vid_url:
                    print(f"  [Agnes] Downloading video from {vid_url} ...")
                    dl_cmd = ["curl", "-s", "-o", output_path, vid_url]
                    subprocess.run(dl_cmd, check=True)
                    print(f"  [Agnes] Saved shot to {output_path}")
                    return output_path
                else:
                    print(f"  [Agnes] Status complete but video URL not found in: {st_json}")
            elif status in ["failed", "error"]:
                raise Exception(f"Agnes task failed: {st_json}")

    raise Exception("Agnes video generation timed out after multiple retries.")

def extract_last_frame(video_path, output_png):
    print(f"  [FFmpeg] Extracting last frame from {video_path} -> {output_png}")
    cmd = ["ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path, "-vframes", "1", "-update", "1", output_png]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_png

def concat_videos_with_bgm(video_list, bgm_file, output_mp4):
    print(f"  [FFmpeg] Concatenating {len(video_list)} video streams without audio noise...")
    list_txt = output_mp4 + ".list.txt"
    temp_no_audio = output_mp4 + ".temp_no_audio.mp4"
    with open(list_txt, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")
    
    # 1. Concat video stream only (-an removes segment audio glitches)
    if bgm_file and os.path.exists(bgm_file):
        print(f"  [FFmpeg] Re-encoding video and mixing single continuous BGM track...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", list_txt,
            "-i", bgm_file,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ac", "2", "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
        subprocess.run(cmd, check=True)
    else:
        print("  [FFmpeg] No BGM provided, outputting silent seamless video concat.")
        os.rename(temp_no_audio, output_mp4)

    if os.path.exists(temp_no_audio):
        os.remove(temp_no_audio)
    if os.path.exists(list_txt):
        os.remove(list_txt)

    print(f"  [FFmpeg] Finished! Final output: {output_mp4}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref_img = os.path.join(base_dir, "assets/dance/01_characters/ips/images/C002_Mika_ref.jpeg")
    bgm_file = os.path.join(base_dir, "third_party/OpenMontage/tests/qa/output/music_calm.mp3")
    out_dir = os.path.join(base_dir, "out/demo_dance_20s_v2")
    os.makedirs(out_dir, exist_ok=True)

    print(">>> Starting 20s Dance Video Generation Demo V2 (Full Body & Seamless BGM) <<<")
    initial_url = upload_to_r2(ref_img, "mika_ref_v2.jpeg")

    char_lock = "Full body shot, head to toe completely visible, headroom above head, shoes visible. A beautiful young Korean woman with long dark hair wearing a white camisole top and denim mini skirt, standing on stage with soft blue lighting, 8k resolution, photorealistic"
    
    shots_config = [
        {"id": "shot_01", "prompt": f"{char_lock}. Upbeat dance, lively side-to-side body sway, smiling, natural hand rhythm"},
        {"id": "shot_02", "prompt": f"{char_lock}. Energetic rhythm dance, smooth arm gestures and gentle body hip sway, bright joyful expression"},
        {"id": "shot_03", "prompt": f"{char_lock}. Cheerful dancing movement, playful hand wave and rhythmic waist motion, happy smile"},
        {"id": "shot_04", "prompt": f"{char_lock}. Finishing dance move returning smoothly to initial standing pose, cheerful smile, seamless loop transition"}
    ]

    video_files = []
    current_start_url = initial_url

    for idx, shot in enumerate(shots_config):
        shot_id = shot["id"]
        shot_mp4 = os.path.join(out_dir, f"{shot_id}.mp4")
        shot_png = os.path.join(out_dir, f"{shot_id}_last_frame.png")

        print(f"\n--- Processing Shot {idx+1}/4: {shot_id} ---")
        
        is_last = (idx == len(shots_config) - 1)
        end_url = initial_url if is_last else None

        if os.path.exists(shot_mp4) and os.path.getsize(shot_mp4) > 100000:
            print(f"  [Cache] {shot_mp4} already exists. Skipping generation.")
        else:
            generate_video_shot(
                prompt=shot["prompt"],
                output_path=shot_mp4,
                start_image_url=current_start_url,
                end_image_url=end_url,
                width=768,
                height=1344
            )
        
        video_files.append(shot_mp4)

        if not is_last:
            extract_last_frame(shot_mp4, shot_png)
            current_start_url = upload_to_r2(shot_png)

    final_mp4 = os.path.join(out_dir, "mika_dance_20s_fullbody_bgm.mp4")
    concat_videos_with_bgm(video_files, bgm_file, final_mp4)
    print(f"\n🎉 20s Dance Video Demo V2 completed successfully! Output file: {final_mp4}")

if __name__ == "__main__":
    main()
