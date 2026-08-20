#!/usr/bin/env python3
import math
import wave
import struct
import os

def render_producer_dance_track(wav_path, bpm=120, duration_sec=30.0, style='fitness'):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    beat_interval = 60.0 / bpm
    samples_per_beat = int(sample_rate * beat_interval)
    
    # Chords progression by style (frequencies in Hz)
    PROGRESSIONS = {
        'fitness': [[130.81, 164.81, 196.00], [146.83, 174.61, 220.00], [164.81, 196.00, 246.94], [130.81, 164.81, 196.00]], # C - Dm - Em - C
        'kpop':    [[174.61, 220.00, 261.63], [196.00, 246.94, 293.66], [146.83, 174.61, 220.00], [130.81, 164.81, 196.00]], # F - G - Dm - C
        'street':  [[110.00, 130.81, 164.81], [123.47, 146.83, 174.61], [98.00, 123.47, 146.83], [110.00, 130.81, 164.81]],  # Am - Bdim - G - Am
        'luxury':  [[130.81, 164.81, 196.00, 246.94], [174.61, 220.00, 261.63, 329.63], [146.83, 174.61, 220.00, 261.63], [130.81, 164.81, 196.00, 246.94]] # Cmaj7 - Fmaj7 - Dm7 - Cmaj7
    }
    chords = PROGRESSIONS.get(style, PROGRESSIONS['fitness'])
    
    frames = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        beat_idx = int(t / beat_interval)
        time_in_beat = t - (beat_idx * beat_interval)
        bar_idx = (beat_idx // 4) % len(chords)
        current_chord = chords[bar_idx]
        
        # 1. Kick Drum (Punchy on every downbeat 1, 2, 3, 4)
        kick = 0.0
        if time_in_beat < 0.2:
            env_kick = math.exp(-time_in_beat * 28.0)
            kick_freq = 140.0 * math.exp(-time_in_beat * 32.0) + 45.0
            kick = math.sin(2.0 * math.pi * kick_freq * time_in_beat) * env_kick * 0.7
        
        # 2. Snare / Clap (Beats 2 and 4)
        snare = 0.0
        if (beat_idx % 2 == 1) and time_in_beat < 0.25:
            env_snare = math.exp(-time_in_beat * 18.0)
            noise = ((math.sin(i * 1234.567) % 1.0) * 2.0 - 1.0)
            tone = math.sin(2.0 * math.pi * 210.0 * time_in_beat)
            snare = (noise * 0.6 + tone * 0.4) * env_snare * 0.5
        
        # 3. Hi-Hat (16th notes drive rhythm)
        sixteenth_time = (t * 4.0 / beat_interval) % 1.0
        hihat = 0.0
        if sixteenth_time < 0.08:
            env_hh = math.exp(-sixteenth_time * 45.0)
            hh_noise = ((math.sin(i * 9876.543) % 1.0) * 2.0 - 1.0)
            hihat = hh_noise * env_hh * 0.2
        
        # 4. Synth Melodic Arpeggio & Chords
        arp_idx = int(t * 8.0 / beat_interval) % len(current_chord)
        note_freq = current_chord[arp_idx]
        synth_lead = (math.sin(2.0 * math.pi * note_freq * t) + 0.5 * math.sin(4.0 * math.pi * note_freq * t)) * 0.25
        
        # 5. Bassline (Walking root sub-bass)
        root_freq = current_chord[0] / 2.0
        bass = math.sin(2.0 * math.pi * root_freq * t) * 0.35
        
        # Sum all audio layers
        sample_val = kick + snare + hihat + synth_lead + bass
        
        # Head / Tail smooth micro-fade (0.05s) to eliminate pop sounds
        if t < 0.05:
            sample_val *= (t / 0.05)
        elif t > (duration_sec - 0.05):
            sample_val *= ((duration_sec - t) / 0.05)
        
        # Master limiter & clipping protection
        sample_val = max(-0.95, min(0.95, sample_val))
        val_16bit = int(sample_val * 30000.0)
        frames.extend(struct.pack('<hh', val_16bit, val_16bit))
    
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)
    print(f'  [Audio Director] Rendered {duration_sec}s Producer BGM ({bpm} BPM, {style} style) -> {wav_path}')
    return wav_path

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'test_bgm.wav'
    render_producer_dance_track(out, bpm=120, duration_sec=30.0, style='fitness')
