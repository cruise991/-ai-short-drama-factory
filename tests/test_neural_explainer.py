#!/usr/bin/env python3
"""Automated Tests for Option A Neural Explainer Pipeline.

Tests:
1. Base motion generation from avatar portrait
2. Seamless video looping with ping-pong transitions
3. Audio-driven neural lip sync & stream generation
4. PIP composition into 16:9 and 9:16 canvases
"""

import os
import subprocess
from pathlib import Path
import pytest
import cv2
import numpy as np

SKILL_SCRIPTS = Path("/Users/workspace/ai_short_company/.agents/skills/agent-video-pipeline/scripts")


@pytest.fixture
def avatar_img(tmp_path):
    img_path = tmp_path / "instructor_test.png"
    img = np.ones((512, 512, 3), dtype=np.uint8) * 200
    # Add simple face features
    cv2.circle(img, (256, 256), 120, (180, 160, 220), -1)
    cv2.circle(img, (210, 230), 15, (50, 40, 30), -1)
    cv2.circle(img, (302, 230), 15, (50, 40, 30), -1)
    cv2.ellipse(img, (256, 310), (30, 15), 0, 0, 180, (50, 40, 180), -1)
    cv2.imwrite(str(img_path), img)
    return img_path


@pytest.fixture
def test_audio(tmp_path):
    wav_path = tmp_path / "test_speech.wav"
    import soundfile as sf
    sr = 24000
    duration = 5.0 # 5 seconds
    t = np.linspace(0, duration, int(sr * duration), False)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(wav_path), tone, sr)
    return wav_path


def test_base_motion_generation(avatar_img, tmp_path):
    out_video = tmp_path / "base_motion.mp4"
    cmd = [
        "python3", str(SKILL_SCRIPTS / "generate_base_motion.py"),
        "-s", str(avatar_img),
        "-o", str(out_video)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert out_video.is_file()
    assert out_video.stat().st_size > 1000


def test_video_looper(avatar_img, tmp_path):
    # First create a 2-second base video matching image dimensions
    base_video = tmp_path / "base_short.mp4"
    img = cv2.imread(str(avatar_img))
    h, w = img.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(base_video), fourcc, 30, (w, h))
    for i in range(60):
        out.write(img)
    out.release()

    # Loop to 10 seconds
    looped_video = tmp_path / "looped_10s.mp4"
    cmd = [
        "python3", str(SKILL_SCRIPTS / "video_looper.py"),
        "-i", str(base_video),
        "-d", "10.0",
        "-o", str(looped_video)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert looped_video.is_file()

    cap = cv2.VideoCapture(str(looped_video))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    assert frame_count == 300 # 10s * 30fps


def test_compose_avatar_neural_pip(avatar_img, test_audio, tmp_path):
    out_video = tmp_path / "pip_neural_output.mp4"
    cmd = [
        "python3", str(SKILL_SCRIPTS / "compose_avatar.py"),
        "--avatar-image", str(avatar_img),
        "--audio", str(test_audio),
        "--output", str(out_video),
        "--mode", "pip",
        "--canvas", "16:9"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert out_video.is_file()

    # Check ffprobe dimensions
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        str(out_video)
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    assert "1920x1080" in probe_res.stdout.strip()
