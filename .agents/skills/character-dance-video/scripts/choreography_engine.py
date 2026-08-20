#!/usr/bin/env python3
import os

CHOREO_PATTERNS = {
    'fitness': [
        'Phase 1 Intro: The woman begins high-energy rhythmic warmup dance, stepping side-to-side to the downbeat, lifting hands to chest with radiant confident smile',
        'Phase 2 Build-up: The woman executes athletic body groove, shifting weight dynamically, doing stylish hip bounce and rhythmic arm pumps on the beat',
        'Phase 3 High-Energy Drop: The woman hits the musical climax drop, performing snappy torso twists, energetic hip sway, and sharp side arm extensions timed with the heavy bass',
        'Phase 4 Climax Flow: The woman continues high-intensity dance rhythm, doing dynamic leg taps and energetic arm raises with joyful expression',
        'Phase 5 Rhythm Release: The woman grooves smoothly, doing stylish hip sway and synchronized rhythmic hand claps to the rhythm',
        'Phase 6 Outro Loop Return: The woman smoothly winds down the movement, stepping and lowering arms back into her exact original starting posture to loop seamlessly'
    ],
    'kpop': [
        'Phase 1 Intro: The woman starts with a cute K-pop point dance, doing subtle head tilt and synchronized wrist flower rotation to the beat',
        'Phase 2 Build-up: The woman performs energetic idol choreography, rhythmic hip sway and cute heart hand gesture on the downbeat',
        'Phase 3 Chorus Drop: The woman hits the chorus drop, doing snappy arm waves, dynamic hip isolations, and stylish shoulder shimmy to the explosive beat',
        'Phase 4 Point Move: The woman executes a snappy dance move, spinning body slightly and striking an energetic camera-facing pose',
        'Phase 5 Groove: The woman grooves with bouncy rhythm, doing stylish finger snaps and rhythmic step-touch combinations',
        'Phase 6 Outro Loop Return: The woman smoothly winds down the movement, stepping back into her exact starting posture and striking the opening pose for a perfect loop'
    ],
    'street': [
        'Phase 1 Intro: The woman does rhythmic side-stepping dance moves, hands gently swaying on beat, smiling charmingly',
        'Phase 2 Build-up: The woman continues energetic dance, doing stylish hip sway and elegant arm dance moves on beat',
        'Phase 3 Drop: The woman smoothly transitions into full groove, doing rhythmic leg taps and graceful arm motions perfectly timed to the drop',
        'Phase 4 Swagger: The woman continues graceful dance, swaying her body to upbeat beat with cheerful expression',
        'Phase 5 Flow: The woman does rhythmic sway and arm dance, keeping character look and background completely consistent',
        'Phase 6 Outro Loop Return: The woman completes dance movement, smoothly stepping back into her exact starting posture to loop seamlessly, smiling brightly'
    ],
    'luxury': [
        'Phase 1 Intro: The woman starts slow graceful rhythmic body sway, arms moving in subtle fluid arcs with poised posture',
        'Phase 2 Build-up: The woman performs elegant slow-groove dance, shifting body weight with gentle torso isolations',
        'Phase 3 Climax: The woman transitions into graceful arm waves and light stepping movement, exuding poise and elegance on the musical swell',
        'Phase 4 Pivot: The woman performs stylish 360 degree slow turn, catching the light with radiant smile',
        'Phase 5 Sway: The woman continues sophisticated rhythmic sway and delicate hand gestures',
        'Phase 6 Outro Loop Return: The woman smoothly returns to her exact original starting pose, holding an effortless poised smile for a seamless loop'
    ]
}

def plan_choreography(style='fitness', duration=30, bpm=120, char_lock_prompt=''):
    num_shots = max(1, duration // 5)
    pattern = CHOREO_PATTERNS.get(style, CHOREO_PATTERNS['fitness'])
    
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
    shots = plan_choreography(style='fitness', duration=20, bpm=120, char_lock_prompt='[LOCK]')
    for s in shots:
        print(f"Shot {s['shot_id']} (Loop={s['is_loop_closure']}): {s['action']}")
