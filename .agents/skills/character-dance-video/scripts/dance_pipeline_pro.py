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

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from character_analyzer import analyze_character_and_scene, vision_describe_multiview
from choreography_engine import plan_choreography
from audio_director import prepare_dance_bgm
from video_muxer import robust_video_concat
from quality_auditor import quality_audit_gate
from multi_view_adapter import MultiViewAdapter

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

def generate_video_shot(prompt, output_path, start_image_url=None, end_image_url=None, width=768, height=1344, key_idx=0, is_kneeling_pose=False, is_indoor=False, is_caucasian=False, defensive_negative=""):
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip('/')
    eth_neg = "asian face, east asian face, oriental features, non-western face, " if is_caucasian else "caucasian face, western features, european face, non-asian face, "
    
    if is_kneeling_pose:
        negative_prompt = (
            "cropped head, head cut off, head out of frame, headless body, missing head, missing face, face cut off, "
            "zoomed-in lower body, torso close-up, bottom half only, lower body only, cropped body, waist-down only, "
            + eth_neg + "mature face, sharp masculine jawline, changed face, altered facial identity, "
            "dwarf proportions, stubby legs, average height body, normal proportions, 7-head body ratio, compact build, thick short thighs, short torso, "
            "head turned 180 degrees, backward head, head facing opposite direction of body, neck twist, "
            "head on backwards, exorcist head rotation, broken neck, unnatural spinal twist, chest on back, "
            "disconnected head rotation, head rotating independently from torso, head-body rotation mismatch, "
            "shoulders facing different direction than hips, unnatural neck angle exceeding 90 degrees, twisted spine beyond anatomical range, "
            "elongated skirt, lengthened dress, changed garment length, garment below original hemline, modified clothing proportions, different outfit from reference, "
            "back of jacket on front, front clothing on back, torso orientation mismatch, mismatched facing direction, "
            "room change, furniture, sofas, indoor living room, bright room, "
            "blurry, low quality, distorted hands, distorted body, extra limbs, ugly face, disjointed limbs, floating head, floating body"
        )
        prompt_suffix = ", maintaining ultra-tall willowy 9-head supermodel body proportions throughout with legs occupying 55 percent of total body height when standing, graceful fluid anatomical motion with natural coordinated head-torso rotation, never compressed shortened or squatting, identical clothing including identical garment length and hemline position and face"
    elif is_indoor:
        negative_prompt = (
            "cropped head, head cut off, head out of frame, headless body, missing head, missing face, face cut off, "
            "zoomed-in lower body, torso close-up, bottom half only, lower body only, cropped body, waist-down only, "
            + eth_neg + "mature face, sharp masculine jawline, sharp angular jawline, prominent high cheekbones, deep nasolabial folds, mature aged face, sunken cheeks, harsh facial lighting, changed face, altered facial identity, "
            "zooming in, camera push in, camera moving forward, dolly forward, camera zoom in, moving closer to camera, closer framing, tight shot, chest up shot, torso close-up, cropped top of head, "
            "blush, cheek blush, flushed cheeks, pink cheeks, red cheeks, blushing, sunburn cheeks, heavy blush makeup, rosacea, "
            "black underwear edge, separate black panties waistband, exposed black briefs, black underwear trim, black bottom edge, peaking underwear waistband, separate underwear, "
            "cutout holes, torn fabric, stomach cutout, belly cutout, torn mesh, holes in clothing, fabric tear, revealing stomach through holes, "
            "high-cut leg opening, high-leg cut, exposed panties on hips, high underwear waistband, riding up top, rolled up hem, shortened top, "
            "heavy eye makeup, dark eyeshadow, eyeliner wings, mature face, elongated face, mature jawline, "
            "houndstooth, plaid skirt, checkered skirt, pattern on skirt, double shoulder straps, symmetric straps, two straps, turning completely backwards, 180-degree turn, back facing camera, spinning 180 degrees, twisting body 180 degrees, "
            "thin face, narrow chin, v-shape face, pointed chin, wide open mouth, big toothy smile, visible teeth, "
            "big belly, potbelly, bloated stomach, protruding belly, pregnant belly, swollen abdomen, thick waist, wide waist, deformed body proportions, deformed abdomen, "
            "dwarf proportions, stubby legs, short torso, "
            "head turned 180 degrees, backward head, head facing opposite direction of body, neck twist, "
            "head on backwards, exorcist head rotation, broken neck, unnatural spinal twist, chest on back, "
            "disconnected head rotation, head rotating independently from torso, head-body rotation mismatch, "
            "shoulders facing different direction than hips, unnatural neck angle exceeding 90 degrees, twisted spine beyond anatomical range, "
            "elongated skirt, lengthened dress, changed garment length, garment below original hemline, modified clothing proportions, different outfit from reference, "
            "back of jacket on front, front clothing on back, torso orientation mismatch, mismatched facing direction, unnatural body rotation, spinning away, "
            "outdoor, street, beach, stage, scene change, background change, disappearing sofa, missing sofa, missing piggy bank, distorted furniture, "
            "blurry, low quality, distorted hands, distorted body, extra limbs, ugly face, disjointed limbs, floating head, floating body"
        )
        prompt_suffix = ", stationary locked-off tripod camera at fixed constant focal distance without zooming in, maintaining exact faithful character body proportions, bust-waist-hip silhouette, and gentle youthful facial identity throughout, perfectly even natural pale skin tone strictly without blush or redness on cheeks, soft natural facial contours, gentle eyes and lips, identical clothing including continuous intact sheer mesh top with solid un-torn fabric covering abdomen down to upper thighs with strictly NO cutout holes and NO separate underwear waistband on hips, strict biomechanical head-torso coordination, natural graceful figure faithful to the reference image, seamless rhythm motion, consistent scene setting across all frames"
    else:
        negative_prompt = (
            "cropped head, head cut off, head out of frame, headless body, missing head, missing face, face cut off, "
            "zoomed-in lower body, torso close-up, bottom half only, lower body only, cropped body, waist-down only, "
            + eth_neg + "mature face, sharp masculine jawline, sharp angular jawline, prominent high cheekbones, deep nasolabial folds, mature aged face, sunken cheeks, harsh facial lighting, changed face, altered facial identity, "
            "blush, cheek blush, flushed cheeks, pink cheeks, red cheeks, blushing, sunburn cheeks, heavy blush makeup, rosacea, "
            "black underwear edge, separate black panties waistband, exposed black briefs, black underwear trim, black bottom edge, peaking underwear waistband, separate underwear, "
            "cutout holes, torn fabric, stomach cutout, belly cutout, torn mesh, holes in clothing, fabric tear, revealing stomach through holes, "
            "high-cut leg opening, high-leg cut, exposed panties on hips, high underwear waistband, riding up top, rolled up hem, shortened top, "
            "heavy eye makeup, dark eyeshadow, eyeliner wings, mature face, elongated face, mature jawline, "
            "turning completely backwards, 180-degree turn, back facing camera, spinning 180 degrees, twisting body 180 degrees, "
            "thin face, narrow chin, v-shape face, pointed chin, wide open mouth, big toothy smile, visible teeth, "
            "big belly, potbelly, bloated stomach, protruding belly, pregnant belly, swollen abdomen, thick waist, wide waist, deformed body proportions, deformed abdomen, "
            "dwarf proportions, stubby legs, short torso, "
            "head turned 180 degrees, backward head, head facing opposite direction of body, neck twist, "
            "head on backwards, exorcist head rotation, broken neck, unnatural spinal twist, chest on back, "
            "disconnected head rotation, head rotating independently from torso, head-body rotation mismatch, "
            "shoulders facing different direction than hips, unnatural neck angle exceeding 90 degrees, twisted spine beyond anatomical range, "
            "modified clothing proportions, different outfit from reference, altered garment style, "
            "back of jacket on front, front clothing on back, torso orientation mismatch, mismatched facing direction, unnatural body rotation, spinning away, "
            "scene change, background change, disappearing background elements, distorted scene, distorted background, "
            "blurry, low quality, distorted hands, distorted body, extra limbs, ugly face, disjointed limbs, floating head, floating body"
        )
        prompt_suffix = (
            ", strictly facing camera directly within +-30 degrees golden viewing angle, direct eye contact with camera, "
            "strictly NO back view and NO turning backwards, maintaining exact faithful character body proportions, "
            "bust-waist-hip silhouette, and gentle youthful round oval facial identity with soft blunt chin throughout, "
            "perfectly even natural skin tone strictly without blush or redness on cheeks, soft natural facial contours, "
            "gentle eyes and lips, strictly identical outfit structure, fabric texture, and clothing design matching reference image 100%, "
            "strict biomechanical head-torso coordination within natural cervical spine rotation range, "
            "natural graceful figure faithful to the reference image, seamless rhythm motion, consistent background setting and ambient lighting across all frames"
        )

    if defensive_negative:
        negative_prompt += f", {defensive_negative}"

    video_model = os.getenv("PRODUCTION_VIDEO_MODEL", "agnes-video-2.5-flash")
    aspect_ratio_str = "9:16" if height > width else "16:9"
    size_str = "720P"

    for attempt in range(25):
        api_key = get_api_key(key_idx + attempt)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        full_prompt = prompt + prompt_suffix

        # Support official Agnes Video 2.5 / 2.5-flash schema
        if "2.5" in video_model:
            data = {
                "model": video_model,
                "prompt": full_prompt,
                "mode": "keyframe" if start_image_url else "text",
                "seconds": "5",
                "size": size_str,
                "aspect_ratio": aspect_ratio_str
            }
            if start_image_url:
                data["first_frame"] = start_image_url
            if end_image_url:
                print("  [Agnes API] Mode: Keyframe (Loop Closure with first_frame and last_frame)...")
                data["last_frame"] = end_image_url
        else:
            data = {
                "model": video_model,
                "prompt": full_prompt,
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

        print(f"  [Agnes API] Submitting request (attempt {attempt+1}/25, model: {video_model})... Prompt: {prompt[:60]}...")
        req_body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/videos", data=req_body, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode('utf-8')
            print(f"  [Agnes Warning] HTTP {err.code}: {err_body}")
            time.sleep(6)
            continue
        except Exception as e:
            print(f"  [Agnes Network Warning] {e}")
            time.sleep(6)
            continue

        video_id = res_json.get("video_id") or res_json.get("id") or res_json.get("task_id") or (res_json.get("data", {}) if isinstance(res_json.get("data"), dict) else {}).get("task_id")
        print(f"  [Agnes API] Task ID: {video_id}. Polling status via official endpoint...")
        
        poll_endpoints = [
            f"{base_url.replace('/v1', '')}/agnesapi?video_id={video_id}&model_name={video_model}",
            f"{base_url}/videos/{video_id}"
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
        "-pix_fmt", "rgb24",
        "-vframes", "1", "-update", "1", output_png
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_png


def check_body_proportion(frame_png, min_body_ratio=0.72):
    """Lightweight check: estimate if character fills enough vertical space.
    Returns True if proportion looks acceptable, False if body appears compressed."""
    try:
        # Check 1: Headroom safety check (top 10% of frame must contain light background, not cropped body/neck)
        head_cmd = ["ffmpeg", "-y", "-i", frame_png, "-vf", "crop=iw:ih*0.1:0:0,format=gray", "-f", "rawvideo", "-"]
        head_proc = subprocess.run(head_cmd, capture_output=True, timeout=10)
        if head_proc.stdout and len(head_proc.stdout) > 0:
            avg_top = sum(head_proc.stdout) / len(head_proc.stdout)
            if avg_top < 105:
                print(f"  [Headroom Alert] Top 10% avg gray is {avg_top:.1f} (<105). Head appears cropped out!")
                return False

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


def check_face_integrity(frame_png):
    """Audit if the frame contains a valid, visible frontal face.
    Returns True if face is present and frontal, False if back of head or missing face."""
    try:
        import cv2
        import numpy as np
        img = cv2.imread(frame_png)
        if img is None:
            return False
        h, w = img.shape[:2]
        # Head & face region: vertical 10%~35%, horizontal 25%~75%
        y1, y2 = int(0.10 * h), int(0.35 * h)
        x1, x2 = int(0.25 * w), int(0.75 * w)
        face_roi = img[y1:y2, x1:x2]
        if face_roi.size == 0:
            return False

        # Convert to YCrCb for skin color detection
        ycrcb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2YCrCb)
        cr = ycrcb[:, :, 1]
        cb = ycrcb[:, :, 2]
        # Typical East Asian skin color range: 133 <= Cr <= 173 and 77 <= Cb <= 127
        skin_mask = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)
        skin_ratio = float(np.sum(skin_mask)) / float(face_roi.shape[0] * face_roi.shape[1])

        # Check hair/dark pixels ratio (back of head typically has >65% dark hair pixels and <8% skin)
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        dark_mask = gray < 60
        dark_ratio = float(np.sum(dark_mask)) / float(face_roi.shape[0] * face_roi.shape[1])

        print(f"  [Face Integrity Check] Skin ratio: {skin_ratio:.1%}, Dark hair ratio: {dark_ratio:.1%}")

        if skin_ratio < 0.08 and dark_ratio > 0.60:
            print("  [Face Integrity Alert] Back of head detected! Face is not facing camera.")
            return False

        if skin_ratio < 0.05:
            print("  [Face Integrity Alert] Insufficient skin pixels in facial region (face missing or obscured).")
            return False

        return True
    except Exception as e:
        print(f"  [Face Integrity Check] Notice: {e}. Defaulting to True.")
        return True


def face_enhance_video(input_mp4, output_mp4):
    """Enhance facial clarity on the final muxed video.
    
    Dual-track strategy:
    1. If GFPGAN and PyTorch are available, perform frame-by-frame AI facial restoration.
    2. Otherwise, preserve the FFmpeg unsharp/eq enhancement already applied during muxing.
    """
    try:
        from gfpgan import GFPGANer
        import cv2
        import torch

        device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"  [Face Enhance] Initializing GFPGANer (model v1.3, device={device})...")

        restorer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=1,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=None,
            device=torch.device(device)
        )

        cap = cv2.VideoCapture(input_mp4)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0 or width <= 0 or height <= 0:
            raise ValueError(f"Invalid input video metadata: {total_frames} frames, {width}x{height}")

        temp_enhanced_raw = output_mp4 + ".enhanced_raw.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_enhanced_raw, fourcc, fps, (width, height))

        print(f"  [Face Enhance] Restoring faces across {total_frames} frames ({width}x{height} @ {fps:.1f}fps)...")
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Weight=0.7 preserves original character identity while sharply enhancing features
            _, _, restored_frame = restorer.enhance(
                frame,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
                weight=0.7
            )
            out.write(restored_frame)
            frame_idx += 1
            if frame_idx % 48 == 0 or frame_idx == total_frames:
                print(f"    [Face Enhance Progress] {frame_idx}/{total_frames} frames ({frame_idx/total_frames*100:.1f}%)")

        cap.release()
        out.release()

        # Remux with audio from input_mp4
        remux_cmd = [
            "ffmpeg", "-y",
            "-i", temp_enhanced_raw,
            "-i", input_mp4,
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-c:a", "copy",
            "-shortest",
            output_mp4
        ]
        subprocess.run(remux_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_enhanced_raw):
            os.remove(temp_enhanced_raw)
        print(f"  [Face Enhance] Successfully enhanced faces and saved -> {output_mp4}")
        return output_mp4

    except Exception as e:
        print(f"  [Face Enhance Notice] AI face restoration skipped: {e}. Keeping high-clarity muxed video.")
        if input_mp4 != output_mp4 and os.path.exists(input_mp4):
            import shutil
            shutil.copy2(input_mp4, output_mp4)
        return output_mp4

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
    parser.add_argument("--tenant-id", default="default", help="SaaS tenant ID for multi-tenant path isolation")
    parser.add_argument("--aspect-ratio", default="9:16", choices=["9:16", "16:9"], help="Video aspect ratio: 9:16 (portrait default) or 16:9 (landscape)")
    parser.add_argument("--selected-view-index", type=int, default=None, help="Explicitly selected viewpoint slice index for start frame")
    parser.add_argument("--enable-face-enhance", action="store_true", default=True, help="Enable HD face enhancement")
    parser.add_argument("--disable-face-enhance", dest="enable_face_enhance", action="store_false", help="Disable HD face enhancement")
    args = parser.parse_args()

    num_shots = max(1, args.duration // 5)
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    
    # Task Isolation: derive unique task prefix and dedicated work directory
    task_prefix = os.path.splitext(os.path.basename(args.output))[0]
    task_work_dir = os.path.join(out_dir, "runs", task_prefix)
    os.makedirs(task_work_dir, exist_ok=True)

    # Resolution calculation based on aspect ratio
    if args.aspect_ratio == "16:9":
        video_w, video_h = 1280, 704
    else:
        video_w, video_h = 704, 1280

    print(f"\n========================================================")
    print(f"🚀 Universal Character Dance Pipeline Pro ({args.duration}s, {num_shots} Shots, Style: {args.style.upper()}, BPM: {args.bpm})")
    print(f"📁 Tenant ID: {args.tenant_id} | Aspect Ratio: {args.aspect_ratio} ({video_w}x{video_h}) | Task Workdir: {task_work_dir}")
    if args.template:
        print(f"🎯 Template Mode: {args.template}")
    print(f"========================================================\n")

    print("\n>>> Step 1: Universal N-View Adaptive Perception & Slicing <<<")
    adapter = MultiViewAdapter(debug=True, aspect_ratio=args.aspect_ratio)
    mv_res = adapter.run_pipeline(
        args.input_image,
        task_work_dir,
        tenant_id=args.tenant_id,
        project_id=task_prefix,
        aspect_ratio=args.aspect_ratio
    )
    detected_n = mv_res["detected_n"]
    is_multiview = mv_res["is_multiview"]
    
    # Resolve start frame: explicit selection or AI-recommended Front view
    if args.selected_view_index is not None and args.selected_view_index < len(mv_res["views"]):
        chosen_view = mv_res["views"][args.selected_view_index]
        primary_front_path = chosen_view["path"]
        print(f"  [Human-in-the-Loop] User explicitly selected View {args.selected_view_index} ({chosen_view['role']}) -> {primary_front_path}")
    else:
        primary_front_path = mv_res["primary_front_path"]
        print(f"  [AI Auto-Anchor] Anchored Front View (100% Single Person) -> {primary_front_path}")

    print(f"  [R2 Upload] Uploading primary start frame to Cloud...")
    initial_url = upload_to_r2(primary_front_path, f"{task_prefix}_front_{os.path.basename(primary_front_path)}")

    multiview_graph = None
    if is_multiview:
        print("  [Step 1.5] Multi-View detected! Extracting 360° Vision Graph & Defense via Agnes 2.5 Flash...")
        turnaround_url = upload_to_r2(args.input_image, f"{task_prefix}_turnaround_full_{os.path.basename(args.input_image)}")
        multiview_graph = vision_describe_multiview(turnaround_url)

    print("\n>>> Step 2: AI Vision Character & Scene Feature Analysis <<<")
    char_meta = analyze_character_and_scene(
        primary_front_path,
        user_desc=args.prompt_desc,
        style_hint=args.style,
        image_url=initial_url,
        is_multiview=is_multiview,
        multiview_graph=multiview_graph
    )
    char_lock_prompt = char_meta["full_prompt_lock"]
    defensive_negative = char_meta.get("defensive_negative", "")
    print(f"  [Prompt Lock]: {char_lock_prompt[:120]}...")
    if defensive_negative:
        print(f"  [Defensive Negatives Active]: {defensive_negative}")

    print("\n>>> Step 3: Planning Professional Choreography <<<")
    is_kneeling = char_meta.get("is_kneeling_pose", False)
    is_indoor = char_meta.get("is_indoor", False)
    is_caucasian = char_meta.get("is_caucasian", False)
    shots = plan_choreography(style=args.style, duration=args.duration, bpm=args.bpm, char_lock_prompt=char_lock_prompt, template_id=args.template, is_rear_pose=char_meta.get("is_rear_pose", False), is_kneeling_pose=is_kneeling, is_indoor=is_indoor)

    video_files = []
    current_start_url = initial_url
    end_url = initial_url

    print(f"\n>>> Step 4: Generating {num_shots} Shots with Chaining & Loop Closure <<<")
    for i, shot in enumerate(shots):
        shot_id = shot["shot_id"]
        is_last = shot["is_loop_closure"]
        shot_mp4 = os.path.join(task_work_dir, f"{task_prefix}_shot_{shot_id:02d}.mp4")
        shot_png = os.path.join(task_work_dir, f"{task_prefix}_shot_{shot_id:02d}_last_frame.png")

        # Phase 2: Chain-propagation safety anchoring
        shot_prompt = shot["prompt"]
        if i == 0:
            # First shot: strict pixel-faithful anchoring to reference image
            shot_prompt += (
                ". CRITICAL FIRST SHOT: This is the opening shot. The character clothing, "
                "garment length, hemline position, body proportions, and all visual details "
                "must be 100 percent pixel-faithful to the reference image with zero deviation"
            )
        else:
            # Subsequent shots: reinforce garment consistency from original reference
            shot_prompt += (
                ". Maintain identical clothing and garment dimensions including identical "
                "exact shorts or pants or skirt fit, garment cut, and hemline position from the original reference character image "
                "throughout this entire shot"
            )

        if os.path.exists(shot_mp4) and os.path.getsize(shot_mp4) > 200000:
            print(f"\n  [Shot {shot_id}/{num_shots}] Found existing valid shot in current task -> {shot_mp4} (Resume)")
        else:
            if is_last:
                print(f"\n  [Shot {shot_id}/{num_shots}] Keyframes Loop Closure Mode ({video_w}x{video_h})...")
                generate_video_shot(shot_prompt, shot_mp4, current_start_url, end_url, width=video_w, height=video_h, key_idx=i, is_kneeling_pose=is_kneeling, is_indoor=is_indoor, is_caucasian=is_caucasian, defensive_negative=defensive_negative)
            else:
                print(f"\n  [Shot {shot_id}/{num_shots}] Chaining Mode ({video_w}x{video_h})...")
                generate_video_shot(shot_prompt, shot_mp4, current_start_url, width=video_w, height=video_h, key_idx=i, is_kneeling_pose=is_kneeling, is_indoor=is_indoor, is_caucasian=is_caucasian, defensive_negative=defensive_negative)

        video_files.append(shot_mp4)

        if not is_last:
            if not (os.path.exists(shot_png) and os.path.getsize(shot_png) > 50000):
                print(f"  [Extract & Upload] Shot {shot_id} last frame (Lossless + Unsharp) -> R2...")
                extract_last_frame_lossless(shot_mp4, shot_png)
                min_prop = 0.60 if is_indoor else 0.72
                has_prop = check_body_proportion(shot_png, min_body_ratio=min_prop)
                has_face = check_face_integrity(shot_png)
                if not has_prop:
                    print(f"  [Safety Fallback] Shot {shot_id} frame body proportion invalid or head cropped - falling back to initial reference image for next shot!")
                    current_start_url = initial_url
                elif not has_face:
                    print(f"  [Safety Fallback] Shot {shot_id} frame missing frontal face (back of head or obscured)! Triggering Face Latent Collapse Protection: falling back to initial reference image for next shot!")
                    current_start_url = initial_url
                else:
                    current_start_url = upload_to_r2(shot_png, f"{task_prefix}_{args.style}_shot_{shot_id:02d}_last.png")
            else:
                print(f"  [Resume] Using existing Shot {shot_id} last frame -> {shot_png}")
                min_prop = 0.60 if is_indoor else 0.72
                has_prop = check_body_proportion(shot_png, min_body_ratio=min_prop)
                has_face = check_face_integrity(shot_png)
                if not has_prop:
                    print(f"  [Safety Fallback] Resume Shot {shot_id} frame body proportion invalid - falling back to initial reference image!")
                    current_start_url = initial_url
                elif not has_face:
                    print(f"  [Safety Fallback] Resume Shot {shot_id} frame missing frontal face - falling back to initial reference image!")
                    current_start_url = initial_url
                else:
                    current_start_url = upload_to_r2(shot_png, f"{task_prefix}_{args.style}_shot_{shot_id:02d}_last.png")

    print("\n>>> Step 5: Audio Director Preparing Master BGM Track <<<")
    bgm_path = os.path.join(task_work_dir, f"{task_prefix}_bgm_{args.duration}s.wav")
    prepare_dance_bgm(bgm_path, duration_sec=float(args.duration), style=args.style, template_id=args.template, custom_bgm=args.bgm, bpm=args.bpm)

    print("\n>>> Step 6: Safe Two-Step Muxing & Encoding <<<")
    temp_muxed_output = args.output + ".muxed.mp4" if getattr(args, "enable_face_enhance", True) else args.output
    robust_video_concat(video_files, bgm_path, temp_muxed_output)

    print("\n>>> Step 7: HD Face Enhancement (Dual-Track AI/Filter) <<<")
    if getattr(args, "enable_face_enhance", True):
        face_enhance_video(temp_muxed_output, args.output)
        if os.path.exists(temp_muxed_output) and temp_muxed_output != args.output:
            try:
                os.remove(temp_muxed_output)
            except Exception:
                pass
    else:
        print("  [Face Enhance] Skipped by flag.")

    print("\n>>> Step 8: Tri-Tier Quality Audit Gate Assertion <<<")
    quality_audit_gate(args.output, reference_image_path=primary_front_path)
    print(f"🎉 Skill Execution Completed! Output File: {args.output}\n")

if __name__ == "__main__":
    main()
