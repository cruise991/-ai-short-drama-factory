import json
import struct
import subprocess

def quality_audit_gate(mp4_path):
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
    print("🎉 All Quality Audit Gates Passed! Video is verified playable & synced!\n")
    return True
