#!/usr/bin/env python3
"""
Compatibility wrapper redirecting to Audio Director Pro
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from audio_director import prepare_dance_bgm

def generate_sync_bpm_music(wav_path, bpm=120, duration_sec=20.0, style='kpop'):
    return prepare_dance_bgm(wav_path, duration_sec=duration_sec, style=style, bpm=bpm)
