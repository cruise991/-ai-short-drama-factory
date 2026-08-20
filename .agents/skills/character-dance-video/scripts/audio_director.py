#!/usr/bin/env python3
import os
import sys
import math
import wave
import struct
import subprocess

def get_bgm_library_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), 'assets', 'bgm_library')

def process_real_audio_track(src_audio_path, output_wav_path, duration_sec=20.0):
    fade_out_start = max(0.0, duration_sec - 0.2)
    af_filters = f"afade=t=in:ss=0:d=0.05,afade=t=out:st={fade_out_start}:d=0.2,loudnorm=I=-14:TP=-1.5:LRA=11"
    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',
        '-i', src_audio_path,
        '-t', str(duration_sec),
        '-af', af_filters,
        '-ar', '44100',
        '-ac', '2',
        output_wav_path
    ]
    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  [Audio Director] Mastered Real Dance BGM -> {output_wav_path} ({duration_sec}s)")
    return output_wav_path

def synthesize_studio_dance_track(wav_path, bpm=128, duration_sec=20.0, style='fitness'):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    beat_interval = 60.0 / bpm
    
    PROGRESSIONS = {
        'fitness': [[130.81, 164.81, 196.00], [146.83, 174.61, 220.00], [164.81, 196.00, 246.94], [130.81, 164.81, 196.00]],
        'kpop':    [[174.61, 220.00, 261.63], [196.00, 246.94, 293.66], [146.83, 174.61, 220.00], [130.81, 164.81, 196.00]],
        'street':  [[110.00, 130.81, 164.81], [123.47, 146.83, 174.61], [98.00, 123.47, 146.83], [110.00, 130.81, 164.81]],
        'luxury':  [[130.81, 164.81, 196.00, 246.94], [174.61, 220.00, 261.63, 329.63], [146.83, 174.61, 220.00, 261.63], [130.81, 164.81, 196.00, 246.94]]
    }
    chords = PROGRESSIONS.get(style, PROGRESSIONS['fitness'])
    
    frames = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        beat_idx = int(t / beat_interval)
        time_in_beat = t - (beat_idx * beat_interval)
        bar_idx = (beat_idx // 4) % len(chords)
        current_chord = chords[bar_idx]
        
        # Arrangement Dynamics: Build-up and Drop
        is_intro = (t < 3.0)
        is_drop = (t >= 6.0 and t < (duration_sec - 2.5))
        is_outro = (t >= (duration_sec - 2.5))
        energy_mult = 1.35 if is_drop else (0.8 if is_intro else 1.0)
        
        # 1. 808 Sub-Bass Kick (Punchy transient + warm low end)
        kick = 0.0
        if time_in_beat < 0.25:
            env_k = math.exp(-time_in_beat * 24.0)
            k_freq = 160.0 * math.exp(-time_in_beat * 35.0) + 48.0
            click = (1.0 if time_in_beat < 0.005 else 0.0) * 0.4
            kick = (math.sin(2.0 * math.pi * k_freq * time_in_beat) + click) * env_k * 0.85 * energy_mult
        
        # 2. Snare / Clap (Beats 2 and 4)
        snare = 0.0
        if not is_intro and (beat_idx % 2 == 1) and time_in_beat < 0.28:
            env_s = math.exp(-time_in_beat * 16.0)
            noise = ((math.sin(i * 3456.789) % 1.0) * 2.0 - 1.0)
            body = math.sin(2.0 * math.pi * 230.0 * time_in_beat)
            snare = (noise * 0.75 + body * 0.25) * env_s * 0.7 * energy_mult
        
        # 3. Hi-Hat (16th note syncopated groove)
        sixteenth_idx = int(t * 4.0 / beat_interval)
        sixteenth_time = (t * 4.0 / beat_interval) % 1.0
        hihat = 0.0
        if not is_intro and sixteenth_time < 0.06:
            accent = 1.2 if (sixteenth_idx % 4 == 2) else 0.8
            env_hh = math.exp(-sixteenth_time * 50.0)
            hh_noise = ((math.sin(i * 8765.432) % 1.0) * 2.0 - 1.0)
            hihat = hh_noise * env_hh * 0.3 * accent * energy_mult
        
        # 4. Melodic Synth Chords & Lead Arpeggio
        arp_idx = int(t * 8.0 / beat_interval) % len(current_chord)
        freq = current_chord[arp_idx]
        synth_harmonics = math.sin(2.0 * math.pi * freq * t) + 0.4 * math.sin(4.0 * math.pi * freq * t) + 0.2 * math.sin(6.0 * math.pi * freq * t)
        synth_lead = synth_harmonics * 0.35 * energy_mult
        
        # 5. Deep 808 Sub-Bass (Drops hard on Chorus)
        root_freq = current_chord[0] / 2.0
        sub_bass = math.sin(2.0 * math.pi * root_freq * t) * (0.5 if is_drop else 0.25)
        
        sample_left = kick + (snare * 0.9) + (hihat * 0.8) + (synth_lead * 0.85) + sub_bass
        sample_right = kick + (snare * 1.1) + (hihat * 1.2) + (synth_lead * 1.15) + sub_bass
        
        # Anti-pop smooth micro-fades
        if t < 0.05:
            fade = t / 0.05
            sample_left *= fade
            sample_right *= fade
        elif t > (duration_sec - 0.1):
            fade = (duration_sec - t) / 0.1
            sample_left *= fade
            sample_right *= fade
        
        sample_left = max(-0.95, min(0.95, sample_left))
        sample_right = max(-0.95, min(0.95, sample_right))
        val_l = int(sample_left * 29000.0)
        val_r = int(sample_right * 29000.0)
        frames.extend(struct.pack('<hh', val_l, val_r))
    
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)
    print(f"  [Audio Director] Rendered {duration_sec}s Studio Producer Track ({bpm} BPM, {style} style) -> {wav_path}")
    return wav_path

def prepare_dance_bgm(output_wav_path, duration_sec=20.0, style='fitness', custom_bgm=None, bpm=120):
    # Priority 1: Explicit custom audio file provided by user
    if custom_bgm and os.path.exists(custom_bgm) and os.path.getsize(custom_bgm) > 10000:
        print(f"  [Audio Director] Using custom audio file: {custom_bgm}")
        return process_real_audio_track(custom_bgm, output_wav_path, duration_sec=duration_sec)
    
    # Priority 2: Pre-mastered library track if valid & audible
    lib_dir = get_bgm_library_path()
    cand_path = os.path.join(lib_dir, f"{style}.mp3")
    if os.path.exists(cand_path) and os.path.getsize(cand_path) > 10000:
        return process_real_audio_track(cand_path, output_wav_path, duration_sec=duration_sec)
    
    # Priority 3: Studio Dynamic Multi-Layer Synthesizer
    return synthesize_studio_dance_track(output_wav_path, bpm=bpm, duration_sec=duration_sec, style=style)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/test_prepared_bgm.wav'
    prepare_dance_bgm(out, duration_sec=20.0, style='fitness')
