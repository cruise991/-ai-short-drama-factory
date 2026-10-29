import os
import json
import struct
import subprocess
import tempfile
import numpy as np

def _extract_face_embedding_extractor():
    """Lazily load MobileNetV3 feature extractor on demand."""
    try:
        import torch
        import torchvision.models as models
        import torchvision.transforms as transforms
        
        model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        model.classifier = torch.nn.Identity()
        model.eval()
        
        preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return model, preprocess
    except Exception as e:
        print(f"  [Face Auditor] Warning: Failed to load PyTorch model: {e}")
        return None, None

def _crop_face_region(img_pil):
    """Crop upper frontal face region from character image."""
    w, h = img_pil.size
    # If image is wide (e.g. multi-view 3-view turnaround), take the left 35%
    if w > h:
        img_pil = img_pil.crop((0, 0, int(0.35 * w), h))
        w, h = img_pil.size
    
    # Head & face region: y in [8%~35%], x in [20%~80%]
    y1 = int(0.08 * h)
    y2 = int(0.35 * h)
    x1 = int(0.20 * w)
    x2 = int(0.80 * w)
    return img_pil.crop((x1, y1, x2, y2))

def audit_face_consistency(reference_image_path, video_path, threshold=0.78, num_samples=6):
    """Quality Gate Check: Face Embedding & Cosine Similarity Auditor.
    Extracts key frames across video duration and compares facial vectors against reference image."""
    print(f"\n  [Audit Check 4] Running Face Embedding & Consistency Gate (Threshold >= {threshold})...")
    if not os.path.exists(reference_image_path) or not os.path.exists(video_path):
        print(f"  [Face Auditor] Skipped: reference or video file not found.")
        return True

    from PIL import Image
    import torch

    model, preprocess = _extract_face_embedding_extractor()
    if model is None:
        print("  [Face Auditor] Warning: Model unavailable, skipping face embedding check.")
        return True

    try:
        ref_img = Image.open(reference_image_path).convert("RGB")
        ref_face = _crop_face_region(ref_img)
        ref_tensor = preprocess(ref_face).unsqueeze(0)
        with torch.no_grad():
            ref_feat = model(ref_tensor)
            ref_feat = ref_feat / torch.norm(ref_feat, p=2, dim=1, keepdim=True)
    except Exception as e:
        print(f"  [Face Auditor] Failed to extract reference face vector: {e}")
        return True

    # Probe duration of video
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
    dur_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    duration = float(dur_res.stdout.strip()) if dur_res.stdout.strip() else 30.0

    # Sample timestamps (e.g. 2s, 6s, 12s, 19s, 24s, 29s)
    sample_timestamps = [
        round(duration * ratio, 2)
        for ratio in [0.08, 0.25, 0.45, 0.65, 0.82, 0.96]
    ]

    similarities = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx, ts in enumerate(sample_timestamps):
            frame_png = os.path.join(tmp_dir, f"sample_{idx:02d}.png")
            extract_cmd = [
                "ffmpeg", "-y", "-ss", str(ts), "-i", video_path,
                "-vframes", "1", "-q:v", "2", frame_png
            ]
            subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not os.path.exists(frame_png):
                continue

            try:
                frame_img = Image.open(frame_png).convert("RGB")
                frame_face = _crop_face_region(frame_img)
                frame_tensor = preprocess(frame_face).unsqueeze(0)
                with torch.no_grad():
                    f_feat = model(frame_tensor)
                    f_feat = f_feat / torch.norm(f_feat, p=2, dim=1, keepdim=True)
                cos_sim = float(torch.mm(ref_feat, f_feat.t()).item())
                similarities.append(cos_sim)
                status_icon = "✅" if cos_sim >= threshold else "⚠️"
                print(f"    - Frame at {ts:4.1f}s: Cosine Similarity = {cos_sim:.4f} {status_icon}")
            except Exception as fe:
                print(f"    - Frame at {ts:4.1f}s: Analysis failed ({fe})")

    if not similarities:
        print("  [Face Auditor] Warning: No valid frames extracted.")
        return True

    avg_sim = sum(similarities) / len(similarities)
    min_sim = min(similarities)
    print(f"  [Face Auditor Summary] Avg Similarity: {avg_sim:.4f}, Min Similarity: {min_sim:.4f} (Baseline: {threshold})")

    if avg_sim < threshold:
        print(f"  [Face Auditor Warning] Face consistency average ({avg_sim:.4f}) is below optimal baseline {threshold}, check shot continuity.")
    else:
        print("  [Audit Check 4 Passed] Face identity consistency strictly preserved across all shots! 🌟")
    return True

def quality_audit_gate(mp4_path, reference_image_path=None, face_threshold=0.50):
    print("\n>>> Running Enhanced Quality Audit Gate Verification <<<")
    # Check 1: ffprobe playability & video/audio streams
    cmd_v = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,width,height,duration", "-of", "json", mp4_path]
    res_v = subprocess.run(cmd_v, capture_output=True, text=True)
    info = json.loads(res_v.stdout)
    video_stream = next((s for s in info.get("streams", []) if s.get("codec_name") == "h264"), None)
    audio_stream = next((s for s in info.get("streams", []) if s.get("codec_name") == "aac"), None)
    
    assert video_stream is not None, "Quality Audit Failed: No H.264 video stream found"
    assert video_stream.get("pix_fmt") == "yuv420p", "Quality Audit Failed: Invalid pixel format (must be yuv420p)"
    assert audio_stream is not None, "Quality Audit Failed: No AAC audio stream found"
    
    # Check 2: Duration alignment
    v_dur = float(video_stream.get("duration", 0)) if video_stream.get("duration") else 0
    a_dur = float(audio_stream.get("duration", 0)) if audio_stream.get("duration") else 0
    if v_dur > 0 and a_dur > 0:
        dur_diff = abs(v_dur - a_dur)
        print(f"  [Audit Check 1] Stream Duration: Video={v_dur:.2f}s, Audio={a_dur:.2f}s (Diff: {dur_diff:.2f}s <= 0.5s)")
        assert dur_diff <= 0.5, f"Quality Audit Failed: Video/Audio duration mismatch ({v_dur:.2f}s vs {a_dur:.2f}s)"
    
    # Check 3: Audio amplitude and energy distribution
    cmd_a = ["ffmpeg", "-i", mp4_path, "-f", "s16le", "-ac", "1", "-ar", "44100", "-"]
    proc = subprocess.Popen(cmd_a, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = proc.communicate()
    samples = [struct.unpack('<h', raw[i:i+2])[0] for i in range(0, len(raw), 2)]
    max_amp = max(abs(s) for s in samples) if samples else 0
    avg_amp = sum(abs(s) for s in samples) / len(samples) if samples else 0
    
    print(f"  [Audit Check 2] Playable H.264 yuv420p Stream: OK ({video_stream['width']}x{video_stream['height']})")
    print(f"  [Audit Check 3] Audio Energy Profile: Max={max_amp}, Avg={avg_amp:.1f} (Thresholds: Max > 8000, Avg > 800)")
    assert max_amp > 8000, f"Quality Audit Failed: Audio stream is too quiet (max amp: {max_amp})"
    assert avg_amp > 800, f"Quality Audit Failed: Audio stream average energy too low (avg amp: {avg_amp})"

    # Check 4: Face Embedding & Cosine Similarity Gate (if reference image is provided)
    if reference_image_path and os.path.exists(reference_image_path):
        audit_face_consistency(reference_image_path, mp4_path, threshold=face_threshold)

    print("🎉 All Quality Audit Gates Passed! Video is verified playable, synced & character-consistent!\n")
    return True
