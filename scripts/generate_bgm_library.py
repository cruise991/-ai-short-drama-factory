import math
import struct
import wave
import subprocess
import os
import random
import shutil

SAMPLE_RATE = 44100

GENRES = {
    'kpop': {
        'bpm': 128,
        'chords': [
            [220.00, 261.63, 329.63, 440.00],
            [174.61, 220.00, 261.63, 349.23],
            [261.63, 329.63, 392.00, 523.25],
            [196.00, 246.94, 293.66, 392.00],
        ],
        'roots': [110.00, 87.31, 130.81, 98.00],
        'lead_scale': [440.00, 523.25, 587.33, 659.25, 783.99, 880.00],
        'kick_decay': 18.0,
        'has_arp': True
    },
    'fitness': {
        'bpm': 130,
        'chords': [
            [146.83, 174.61, 220.00, 293.66],
            [116.54, 146.83, 174.61, 233.08],
            [174.61, 220.00, 261.63, 349.23],
            [130.81, 164.81, 196.00, 261.63],
        ],
        'roots': [73.42, 58.27, 87.31, 65.41],
        'lead_scale': [293.66, 349.23, 440.00, 523.25, 587.33],
        'kick_decay': 22.0,
        'has_arp': True
    },
    'street': {
        'bpm': 115,
        'chords': [
            [164.81, 196.00, 246.94, 293.66],
            [220.00, 261.63, 329.63, 392.00],
            [246.94, 293.66, 369.99, 440.00],
            [164.81, 196.00, 246.94, 329.63],
        ],
        'roots': [82.41, 110.00, 123.47, 82.41],
        'lead_scale': [329.63, 392.00, 440.00, 493.88, 587.33, 659.25],
        'kick_decay': 16.0,
        'has_arp': False
    },
    'luxury': {
        'bpm': 120,
        'chords': [
            [185.00, 220.00, 277.18, 329.63],
            [146.83, 185.00, 220.00, 277.18],
            [220.00, 277.18, 329.63, 440.00],
            [164.81, 207.65, 246.94, 329.63],
        ],
        'roots': [92.50, 73.42, 110.00, 82.41],
        'lead_scale': [370.00, 440.00, 493.88, 554.37, 659.25],
        'kick_decay': 14.0,
        'has_arp': True
    },
    'thai_sway': {
        'bpm': 108,
        'chords': [
            [130.81, 164.81, 196.00],
            [146.83, 174.61, 220.00],
            [164.81, 196.00, 246.94],
            [130.81, 164.81, 196.00],
        ],
        'roots': [65.41, 73.42, 82.41, 65.41],
        'lead_scale': [261.63, 293.66, 329.63, 392.00, 440.00, 523.25],
        'kick_decay': 24.0,
        'has_arp': True
    },
    'cai_bao_xiao': {
        'bpm': 125,
        'chords': [
            [261.63, 329.63, 392.00],
            [196.00, 246.94, 293.66],
            [220.00, 261.63, 329.63],
            [174.61, 220.00, 261.63],
        ],
        'roots': [130.81, 98.00, 110.00, 87.31],
        'lead_scale': [523.25, 587.33, 659.25, 783.99, 880.00],
        'kick_decay': 18.0,
        'has_arp': True
    },
    'jump_blackpink': {
        'bpm': 128,
        'chords': [
            [110.00, 130.81, 164.81],
            [98.00, 123.47, 146.83],
            [87.31, 110.00, 130.81],
            [82.41, 103.83, 123.47],
        ],
        'roots': [55.00, 49.00, 43.65, 41.20],
        'lead_scale': [440.00, 466.16, 523.25, 587.33, 659.25, 880.00],
        'kick_decay': 26.0,
        'has_arp': True
    },
    'electronic': {
        'bpm': 126,
        'chords': [
            [174.61, 220.00, 261.63],
            [196.00, 246.94, 293.66],
            [220.00, 261.63, 329.63],
            [196.00, 246.94, 293.66],
        ],
        'roots': [87.31, 98.00, 110.00, 98.00],
        'lead_scale': [349.23, 392.00, 440.00, 523.25, 659.25],
        'kick_decay': 18.0,
        'has_arp': True
    }
}

def render_genre_track(genre_name, cfg, target_mp3_path, duration_sec=60.0):
    bpm = cfg['bpm']
    sec_per_beat = 60.0 / bpm
    bar_sec = sec_per_beat * 4.0
    num_samples = int(SAMPLE_RATE * duration_sec)
    
    chords = cfg['chords']
    roots = cfg['roots']
    lead_scale = cfg['lead_scale']
    kick_decay = cfg['kick_decay']
    has_arp = cfg['has_arp']
    
    random.seed(hash(genre_name) % 10000)
    noise_table = [random.uniform(-1.0, 1.0) for _ in range(SAMPLE_RATE)]
    
    raw_wav_path = target_mp3_path + ".temp.wav"
    os.makedirs(os.path.dirname(os.path.abspath(target_mp3_path)), exist_ok=True)
    
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
        if not is_break:
            if time_in_beat < 0.28:
                k_env = math.exp(-time_in_beat * kick_decay)
                k_pitch = 190.0 * math.exp(-time_in_beat * 40.0) + 46.0
                k_sine = math.sin(2.0 * math.pi * k_pitch * time_in_beat)
                click = (noise_table[i % len(noise_table)] * 0.45) if time_in_beat < 0.004 else 0.0
                kick = (k_sine + click) * k_env * 0.95
                
        # 2. Layered Snare / Clap
        snare = 0.0
        if beat_in_bar in [1, 3] and time_in_beat < 0.25:
            s_env = math.exp(-time_in_beat * 16.0)
            s_tone = math.sin(2.0 * math.pi * 215.0 * time_in_beat) * 0.35
            s_noise = noise_table[(i * 3) % len(noise_table)] * 0.65
            snare = (s_tone + s_noise) * s_env * 0.75
        elif is_break and time_in_beat < 0.12:
            s_env = math.exp(-time_in_beat * 20.0)
            snare = noise_table[(i * 5) % len(noise_table)] * s_env * 0.6
            
        # 3. Hi-Hats & Shakers
        hihat = 0.0
        sub_16th = int(frac_beat * 4.0)
        time_in_16th = (frac_beat * 4.0) % 1.0
        if time_in_16th < 0.22:
            hh_env = math.exp(-time_in_16th * 14.0)
            accent = 1.35 if (sub_16th == 2) else 0.75
            hihat = noise_table[(i * 7) % len(noise_table)] * hh_env * 0.22 * accent
        if sub_16th == 2 and 0 < (frac_beat - 0.5) < 0.35:
            oh_time = frac_beat - 0.5
            oh_env = math.exp(-oh_time * 9.0)
            hihat += noise_table[(i * 11) % len(noise_table)] * oh_env * 0.26
            
        # 4. Sub & Mid Bass
        sub_raw = math.sin(2.0 * math.pi * current_root * t) + 0.35 * math.sin(4.0 * math.pi * current_root * t)
        sub = sub_raw * sidechain * 0.50
        
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
        
        # 6. Arp / Pluck Lead
        lead_l = 0.0
        lead_r = 0.0
        if has_arp:
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
        
        val_l = int(mix_l * 32000.0)
        val_r = int(mix_r * 32000.0)
        frames.extend(struct.pack('<hh', val_l, val_r))
        
    with wave.open(raw_wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)
        
    master_filter = "volume=0.85,equalizer=f=60:width_type=o:w=1:g=2,equalizer=f=12000:width_type=o:w=1:g=1.5,loudnorm=I=-14:TP=-1.5:LRA=11"
    cmd = [
        "ffmpeg", "-y", "-i", raw_wav_path,
        "-af", master_filter,
        "-c:a", "libmp3lame", "-b:a", "192k",
        target_mp3_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(raw_wav_path):
        os.remove(raw_wav_path)
    print(f"Master Track Rendered: {target_mp3_path} ({genre_name}, {bpm} BPM)")

if __name__ == '__main__':
    base_dirs = [
        '/Users/workspace/ai_short_company/ai-short-drama/.agents/skills/character-dance-video/assets/bgm_library',
        '/Users/workspace/ai_short_company/ai-short-drama/assets/dance/05_music/tracks'
    ]
    for b in base_dirs:
        os.makedirs(b, exist_ok=True)
        
    for name, cfg in GENRES.items():
        p1 = os.path.join(base_dirs[0], f"{name}.mp3")
        render_genre_track(name, cfg, p1, duration_sec=60.0)
        p2 = os.path.join(base_dirs[1], f"{name}.mp3")
        shutil.copyfile(p1, p2)
