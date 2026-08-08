import math
import struct
import wave

def generate_sync_bpm_music(wav_path, bpm=120, duration_sec=20.0):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    beat_interval = 60.0 / bpm
    
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            beat_pos = (t % beat_interval) / beat_interval
            
            # Rhythm melody: C5, E5, G5, A5 on each bar beat
            notes = [523.25, 659.25, 783.99, 880.00]
            current_note = notes[int(t / beat_interval) % len(notes)]
            
            # Kick drum pulse on beat hit
            kick = math.exp(-beat_pos * 8.0) * math.sin(2 * math.pi * 60.0 * beat_pos) * 0.6
            syn = math.sin(2 * math.pi * current_note * t) * 0.3 * (1.0 - beat_pos * 0.5)
            
            sample_val = int((kick + syn) * 20000)
            sample_val = max(-32768, min(32767, sample_val))
            
            packed = struct.pack('<hh', sample_val, sample_val)
            frames.extend(packed)
            
        wav_file.writeframes(frames)
    return wav_path
