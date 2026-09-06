#!/usr/bin/env python3
"""
Audio Director Pro - High-Fidelity Electronic Dance Music Engine
Features:
  1. P1: User Custom Audio File Support (with auto-looping and EBU R128 mastering)
  2. P2: Template & Style Studio BGM Library (8 rich electronic genres with dynamic BPM atempo stretch)
  3. P3: Procedural Multi-Layer Super-Saw & 808 Synth Fallback
  4. Full EBU R128 broadcast loudness compliance (-14 LUFS, True Peak -1.5dB)
"""

import os
import sys
import math
import wave
import struct
import random
import subprocess

SAMPLE_RATE = 44100

TEMPLATE_GENRE_MAP = {
    'DANCE_GLANCE_SWAY': 'street',
    'DANCE_THAI_SWAY': 'thai_sway',
    'DANCE_CAI_BAO_XIAO': 'cai_bao_xiao',
    'DANCE_JUMP_BLACKPINK': 'jump_blackpink',
    'DANCE_ANGLE_AESPA': 'kpop',
    'DANCE_LEMONADE_AESPA': 'kpop',
    'DANCE_PENGUIN': 'electronic',
    'DANCE_SUBJECT_3': 'electronic',
    'DANCE_CURRY_SONG': 'street',
    'DANCE_GET_ON_BUS': 'street',
    'DANCE_HIME_ME_SHAKE': 'kpop',
    'DANCE_QING_TIAN_DA_LAO_YE': 'cai_bao_xiao',
    'DANCE_REVENGE_SHAKE': 'fitness'
}

GENRE_DEFAULT_BPM = {
    'kpop': 128,
    'fitness': 130,
    'street': 115,
    'luxury': 120,
    'thai_sway': 108,
    'cai_bao_xiao': 125,
    'jump_blackpink': 128,
    'electronic': 126
}

def get_bgm_library_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.join(os.path.dirname(script_dir), 'assets', 'bgm_library')
    p2 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'assets', 'dance', '05_music', 'tracks')
    return [p1, p2]

def master_audio_track(src_audio_path, output_wav_path, duration_sec=30.0, target_bpm=None, base_bpm=None, seamless_loop=True):
    filters = []
    # Dynamic BPM Tempo Stretch if base_bpm and target_bpm are provided
    if target_bpm and base_bpm and base_bpm > 0:
        ratio = float(target_bpm) / float(base_bpm)
        if 0.85 <= ratio <= 1.15 and abs(ratio - 1.0) > 0.02:
            filters.append(f"atempo={ratio:.4f}")
            print(f"  [Audio Director] Applying Tempo Alignment ({base_bpm} -> {target_bpm} BPM, factor: {ratio:.3f})")
            
    if not seamless_loop:
        fade_out_start = max(0.0, duration_sec - 0.3)
        filters.append("afade=t=in:ss=0:d=0.08")
        filters.append(f"afade=t=out:st={fade_out_start:.2f}:d=0.3")
    else:
        # Micro envelope to eliminate DC clicks while maintaining 100% continuous loop energy
        filters.append("afade=t=in:ss=0:d=0.005")
        filters.append(f"afade=t=out:st={duration_sec-0.005:.3f}:d=0.005")
    filters.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    af_str = ",".join(filters)
    
    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',
        '-i', src_audio_path,
        '-t', f"{duration_sec:.2f}",
        '-af', af_str,
        '-ar', '44100',
        '-ac', '2',
        output_wav_path
    ]
    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  [Audio Director] Mastered Professional BGM -> {output_wav_path} ({duration_sec}s, EBU R128 Compliant)")
    return output_wav_path

def synthesize_studio_dance_track(wav_path, bpm=128, duration_sec=30.0, style='kpop'):
    sec_per_beat = 60.0 / bpm
    bar_sec = sec_per_beat * 4.0
    num_samples = int(SAMPLE_RATE * duration_sec)
    
    PROGRESSIONS = {
        'kpop': {
            'chords': [[220.0, 261.6, 329.6, 440.0], [174.6, 220.0, 261.6, 349.2], [261.6, 329.6, 392.0, 523.2], [196.0, 246.9, 293.6, 392.0]],
            'roots': [110.0, 87.3, 130.8, 98.0],
            'lead': [440.0, 523.2, 587.3, 659.2, 783.9, 880.0]
        },
        'fitness': {
            'chords': [[146.8, 174.6, 220.0, 293.6], [116.5, 146.8, 174.6, 233.0], [174.6, 220.0, 261.6, 349.2], [130.8, 164.8, 196.0, 261.6]],
            'roots': [73.4, 58.3, 87.3, 65.4],
            'lead': [293.6, 349.2, 440.0, 523.2, 587.3]
        },
        'street': {
            'chords': [[164.8, 196.0, 246.9, 293.6], [220.0, 261.6, 329.6, 392.0], [246.9, 293.6, 370.0, 440.0], [164.8, 196.0, 246.9, 329.6]],
            'roots': [82.4, 110.0, 123.5, 82.4],
            'lead': [329.6, 392.0, 440.0, 493.8, 587.3, 659.2]
        },
        'luxury': {
            'chords': [[185.0, 220.0, 277.2, 329.6], [146.8, 185.0, 220.0, 277.2], [220.0, 277.2, 329.6, 440.0], [164.8, 207.6, 246.9, 329.6]],
            'roots': [92.5, 73.4, 110.0, 82.4],
            'lead': [370.0, 440.0, 493.8, 554.4, 659.2]
        }
    }
    cfg = PROGRESSIONS.get(style, PROGRESSIONS['kpop'])
    chords = cfg['chords']
    roots = cfg['roots']
    lead_scale = cfg['lead']
    
    random.seed(42)
    noise_table = [random.uniform(-1.0, 1.0) for _ in range(SAMPLE_RATE)]
    
    raw_wav_path = wav_path + ".temp_raw.wav"
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    
    frames = bytearray()
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        beat_total = t / sec_per_beat
        beat_idx = int(beat_total)
        bar_idx = (beat_idx // 4) % len(chords)
        beat_in_bar = beat_idx % 4
        time_in_beat = t - (beat_idx * sec_per_beat)
        frac_beat = time_in_beat / sec_per_beat
        
        current_chord = chords[bar_idx]
        current_root = roots[bar_idx]
        
        total_bar_num = int(t / bar_sec)
        cycle_bar = total_bar_num % 8
        is_break = (cycle_bar in [3, 7] and beat_in_bar >= 2)
        sidechain = min(1.0, max(0.0, time_in_beat / 0.16) ** 1.8) if (not is_break) else 1.0
        
        # 1. 808 Kick
        kick = 0.0
        if not is_break and time_in_beat < 0.28:
            k_env = math.exp(-time_in_beat * 18.0)
            k_pitch = 190.0 * math.exp(-time_in_beat * 40.0) + 46.0
            k_sine = math.sin(2.0 * math.pi * k_pitch * time_in_beat)
            click = (noise_table[i % len(noise_table)] * 0.45) if time_in_beat < 0.004 else 0.0
            kick = (k_sine + click) * k_env * 0.95
            
        # 2. Snare / Clap
        snare = 0.0
        if beat_in_bar in [1, 3] and time_in_beat < 0.25:
            s_env = math.exp(-time_in_beat * 16.0)
            s_tone = math.sin(2.0 * math.pi * 215.0 * time_in_beat) * 0.35
            s_noise = noise_table[(i * 3) % len(noise_table)] * 0.65
            snare = (s_tone + s_noise) * s_env * 0.75
            
        # 3. Hi-Hats
        hihat = 0.0
        sub_16th = int(frac_beat * 4.0)
        time_in_16th = (frac_beat * 4.0) % 1.0
        if time_in_16th < 0.22:
            hh_env = math.exp(-time_in_16th * 14.0)
            accent = 1.35 if (sub_16th == 2) else 0.75
            hihat = noise_table[(i * 7) % len(noise_table)] * hh_env * 0.22 * accent
            
        # 4. Sub-Bass
        sub = (math.sin(2.0 * math.pi * current_root * t) + 0.35 * math.sin(4.0 * math.pi * current_root * t)) * sidechain * 0.50
        
        # 5. Super-Saw Chords
        chord_synth_l = 0.0
        chord_synth_r = 0.0
        pulse = 0.75 + 0.25 * math.sin(2.0 * math.pi * (beat_total * 2.0))
        for f in current_chord:
            saw_l = (2.0 * ((t * f * 0.996) % 1.0) - 1.0) + (2.0 * ((t * f * 1.004) % 1.0) - 1.0)
            saw_r = (2.0 * ((t * f * 0.992) % 1.0) - 1.0) + (2.0 * ((t * f * 1.008) % 1.0) - 1.0)
            chord_synth_l += saw_l * 0.06
            chord_synth_r += saw_r * 0.06
        chord_synth_l *= sidechain * pulse
        chord_synth_r *= sidechain * pulse
        
        # 6. Arp Lead
        note_idx = int(beat_total * 4.0) % len(lead_scale)
        lead_freq = lead_scale[note_idx]
        l_env = math.exp(-time_in_16th * 8.5)
        lead_wave = math.sin(2.0 * math.pi * lead_freq * t) + 0.35 * math.sin(4.0 * math.pi * lead_freq * t)
        pan = math.sin(t * 3.14159)
        lead_l = lead_wave * l_env * 0.28 * (0.5 + 0.5 * pan)
        lead_r = lead_wave * l_env * 0.28 * (0.5 - 0.5 * pan)
        
        mix_l = kick + (snare * 0.9) + (hihat * 0.8) + sub + chord_synth_l + lead_l
        mix_r = kick + (snare * 1.1) + (hihat * 1.2) + sub + chord_synth_r + lead_r
        
        mix_l = math.tanh(mix_l * 1.12) * 0.90
        mix_r = math.tanh(mix_r * 1.12) * 0.90
        
        frames.extend(struct.pack('<hh', int(mix_l * 32000.0), int(mix_r * 32000.0)))
        
    with wave.open(raw_wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)
        
    master_filter = f"afade=t=in:ss=0:d=0.005,afade=t=out:st={duration_sec-0.005:.3f}:d=0.005,loudnorm=I=-14:TP=-1.5:LRA=11"
    cmd = ['ffmpeg', '-y', '-i', raw_wav_path, '-af', master_filter, '-ar', '44100', '-ac', '2', wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(raw_wav_path):
        os.remove(raw_wav_path)
    print(f"  [Audio Director] Procedural Super-Saw Synth Mastered -> {wav_path} ({duration_sec}s, {style}, {bpm} BPM)")
    return wav_path

def prepare_dance_bgm(output_wav_path, duration_sec=30.0, style='kpop', template_id=None, custom_bgm=None, bpm=None):
    # Priority 1: Explicit custom audio file
    if custom_bgm and os.path.exists(custom_bgm) and os.path.getsize(custom_bgm) > 10000:
        print(f"  [Audio Director] Priority 1: Using custom audio file -> {custom_bgm}")
        return master_audio_track(custom_bgm, output_wav_path, duration_sec=duration_sec, target_bpm=bpm)
    
    # Determine Genre from Template or Style
    resolved_genre = 'kpop'
    if template_id and template_id in TEMPLATE_GENRE_MAP:
        resolved_genre = TEMPLATE_GENRE_MAP[template_id]
    elif style:
        style_clean = style.lower().strip()
        resolved_genre = TEMPLATE_GENRE_MAP.get(style_clean, style_clean if style_clean in GENRE_DEFAULT_BPM else 'kpop')
        
    base_bpm = GENRE_DEFAULT_BPM.get(resolved_genre, 128)
    target_bpm = bpm if (bpm and bpm > 0) else base_bpm
    
    # Priority 2: Pre-Mastered Studio BGM Library Track
    lib_dirs = get_bgm_library_paths()
    for d in lib_dirs:
        cand_path = os.path.join(d, f"{resolved_genre}.mp3")
        if os.path.exists(cand_path) and os.path.getsize(cand_path) > 10000:
            print(f"  [Audio Director] Priority 2: Studio Library Track -> {cand_path} (Genre: {resolved_genre.upper()}, Base BPM: {base_bpm})")
            return master_audio_track(cand_path, output_wav_path, duration_sec=duration_sec, target_bpm=target_bpm, base_bpm=base_bpm)
            
    # Priority 3: Procedural Multi-Layer Super-Saw Synthesizer Fallback
    print(f"  [Audio Director] Priority 3: Dynamic Multi-Layer Synthesis (Genre: {resolved_genre}, BPM: {target_bpm})")
    return synthesize_studio_dance_track(output_wav_path, bpm=target_bpm, duration_sec=duration_sec, style=resolved_genre)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/test_prepared_bgm.wav'
    prepare_dance_bgm(out, duration_sec=30.0, style='fitness', template_id='DANCE_THAI_SWAY', bpm=115)
