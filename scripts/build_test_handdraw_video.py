import os
import sys
import json
import subprocess
import wave
from pathlib import Path

PROJECT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_anger_decision")
INPUTS_DIR = PROJECT_DIR / "inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Spoken narration beats
BEATS = [
    {
        "id": "beat_01",
        "text": "你有没有发现，每次在极度愤怒时做出的决定，事后往往都让你后悔莫及？",
        "voice": "Tingting"
    },
    {
        "id": "beat_02",
        "text": "这并不是因为你意志力薄弱，而是你的大脑正在经历一场静默政变。",
        "voice": "Tingting"
    },
    {
        "id": "beat_03",
        "text": "在大脑中，额头后方的前额叶皮层是理性的首席执行官，负责逻辑与长远权衡。",
        "voice": "Tingting"
    },
    {
        "id": "beat_04",
        "text": "而大脑深处的杏仁核则是原始的情绪警报器，专门负责恐惧与愤怒的本能反应。",
        "voice": "Tingting"
    },
    {
        "id": "beat_05",
        "text": "一旦怒火爆发，杏仁核以毫秒级的速度抢夺控制权，强行切断前额叶的逻辑供能，这就是著名的杏仁核劫持。",
        "voice": "Tingting"
    },
    {
        "id": "beat_06",
        "text": "在失去理性把关的瞬间，我们做出的并不是决定，而是远古生存留下的反击冲动。",
        "voice": "Tingting"
    },
    {
        "id": "beat_07",
        "text": "破解这个机制其实非常简单：愤怒激素在大脑中的半衰期只有短短六秒。",
        "voice": "Tingting"
    },
    {
        "id": "beat_08",
        "text": "在爆发前强制停顿六秒，做一次深呼吸，前额叶就会重新恢复供能。别在暴怒时做任何决定。",
        "voice": "Tingting"
    }
]

def synthesize_audio_tracks():
    audio_info = []
    total_sec = 0.0
    for beat in BEATS:
        beat_id = beat["id"]
        text = beat["text"]
        aiff_file = INPUTS_DIR / f"{beat_id}.aiff"
        wav_file = INPUTS_DIR / f"{beat_id}.wav"
        
        # Call macOS native say command
        subprocess.run(["say", "-v", beat["voice"], "-o", str(aiff_file), text], check=True)
        # Convert to standard 48kHz mono 16-bit PCM WAV
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(aiff_file),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_file)
        ], check=True)
        if aiff_file.exists():
            aiff_file.unlink()
            
        with wave.open(str(wav_file), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            
        total_sec += duration
        audio_info.append({
            "id": beat_id,
            "text": text,
            "audio": f"inputs/{beat_id}.wav",
            "duration": round(duration, 3)
        })
        print(f"[{beat_id}] ({duration:.2f}s): {text[:20]}...")
        
    print(f"\nTotal narration duration: {total_sec:.2f} seconds.")
    return audio_info

if __name__ == "__main__":
    synthesize_audio_tracks()
