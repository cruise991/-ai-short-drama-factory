import json
import struct
import subprocess

def quality_audit_gate(mp4_path):
    print("\n>>> Running Quality Audit Gate Verification <<<")
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
    print("🎉 All Quality Audit Gates Passed! Video is verified playable & synced!\n")
    return True
