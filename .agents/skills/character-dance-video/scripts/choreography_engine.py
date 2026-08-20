#!/usr/bin/env python3
import os

CHOREO_PATTERNS = {
    'fitness': [
        'The woman begins high-energy rhythmic warmup dance, stepping side-to-side to the beat, lifting hands to chest with joyful smile',
        'The woman performs energetic fitness body groove, shifting weight dynamically, doing stylish hip bounce and arm pump to the beat',
        'The woman moves into core rhythm dance, doing graceful torso twist and sharp side arm extensions timed to the beat',
        'The woman does dynamic high-energy dance steps, rhythmic leg taps and energetic arm raises with confident expression',
        'The woman continues upbeat athletic dance moves, stylish hip sway and synchronized rhythmic hand claps to the rhythm',
        'The woman transitions smoothly, gracefully stepping and lowering arms back into her exact original starting posture to loop seamlessly'
    ],
    'kpop': [
        'The woman starts with a cute K-pop point dance, doing subtle head tilt and synchronized wrist flower rotation to the beat',
        'The woman performs energetic idol choreography, rhythmic hip sway and cute heart hand gesture on the downbeat',
        'The woman glides smoothly with rhythmic footwork, doing dynamic arm waves and stylish shoulder shimmy to the rhythm',
        'The woman executes a snappy dance move, spinning body slightly and striking an energetic camera-facing pose',
        'The woman grooves with bouncy rhythm, doing stylish finger snaps and rhythmic step-touch combinations',
        'The woman smoothly winds down the movement, stepping back into her exact starting posture and striking the opening pose for a perfect loop'
    ],
    'street': [
        'The woman does rhythmic side-stepping dance moves, hands gently swaying on beat, smiling charmingly',
        'The woman continues energetic dance, doing stylish hip sway and elegant arm dance moves on beat',
        'The woman smoothly transitions dance movement, doing rhythmic leg taps and graceful arm motions perfectly timed',
        'The woman continues graceful dance, swaying her body to upbeat beat with cheerful expression',
        'The woman does rhythmic sway and arm dance, keeping character look and background completely consistent',
        'The woman completes dance movement, smoothly stepping back into her exact starting posture to loop seamlessly, smiling brightly'
    ],
    'luxury': [
        'The woman starts slow graceful rhythmic body sway, arms moving in subtle fluid arcs with poised posture',
        'The woman performs elegant slow-groove dance, shifting body weight with gentle torso isolations',
        'The woman transitions into graceful arm waves and light stepping movement, exuding poise and elegance',
        'The woman performs stylish 360 degree slow turn, catching the light with radiant smile',
        'The woman continues sophisticated rhythmic sway and delicate hand gestures',
        'The woman smoothly returns to her exact original starting pose, holding an effortless poised smile for a seamless loop'
    ]
}

def plan_choreography(style='fitness', duration=30, bpm=120, char_lock_prompt=''):
    num_shots = max(1, duration // 5)
    pattern = CHOREO_PATTERNS.get(style, CHOREO_PATTERNS['fitness'])
    
    # Dynamically scale pattern to match num_shots
    if num_shots <= len(pattern):
        selected = pattern[:num_shots - 1] + [pattern[-1]]
    else:
        selected = []
        for i in range(num_shots - 1):
            selected.append(pattern[i % (len(pattern) - 1)])
        selected.append(pattern[-1])
    
    shots = []
    for i, action in enumerate(selected):
        is_last = (i == len(selected) - 1)
        full_prompt = f'{char_lock_prompt} {action}'
        shots.append({
            'shot_id': i + 1,
            'is_loop_closure': is_last,
            'action': action,
            'prompt': full_prompt,
            'duration_sec': 5
        })
    return shots

if __name__ == '__main__':
    shots = plan_choreography(style='fitness', duration=30, bpm=120, char_lock_prompt='[LOCK]')
    for s in shots:
        print(f"Shot {s['shot_id']} (Loop={s['is_loop_closure']}): {s['prompt']}")
