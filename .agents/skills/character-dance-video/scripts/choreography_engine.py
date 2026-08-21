#!/usr/bin/env python3
import os

CHOREO_PATTERNS = {
    'kpop': [
        'Phase 1 Intro: The woman maintains an ultra-tall erect posture with straight long legs, doing subtle head tilt and synchronized wrist flower rotation to the beat while smiling radiantly',
        'Phase 2 Build-up: The woman executes energetic idol dance moves, keeping legs long and straight, doing rhythmic hip sway and cute heart hand gesture on the downbeat',
        'Phase 3 Chorus Drop: The woman hits the chorus drop with upright posture, doing snappy arm waves, dynamic hip isolations, and stylish shoulder shimmy to the explosive beat',
        'Phase 4 Pose Convergence: The woman smoothly straightens both legs to full tall slender height, places both hands firmly on her waist/hips, turns straight to the front, and settles perfectly into her exact original starting posture for a 100% seamless loop',
        'Phase 5 Groove: The woman grooves with bouncy rhythm while maintaining full height, doing stylish finger snaps and rhythmic step-touch combinations',
        'Phase 6 Final Convergence: The woman smoothly straightens both legs to full tall slender height, places both hands firmly on her waist/hips, turns straight to the front, and settles perfectly into her exact original starting posture for a 100% seamless loop'
    ],
    'fitness': [
        'Phase 1 Intro: The woman maintains an ultra-tall erect posture with straight long legs, beginning rhythmic warmup dance, stepping side-to-side to the downbeat with radiant confident smile',
        'Phase 2 Build-up: The woman executes athletic body groove with straight tall posture, shifting weight dynamically, doing stylish hip bounce and rhythmic arm pumps on the beat',
        'Phase 3 Drop: The woman hits the climax drop with upright posture, performing snappy torso twists, energetic hip sway, and sharp side arm extensions timed with the heavy bass',
        'Phase 4 Pose Convergence: The woman smoothly straightens both legs to full tall slender height, lowers both arms and places hands on hips, standing perfectly upright in her exact starting posture for a 100% seamless loop',
        'Phase 5 Release: The woman grooves smoothly while keeping tall posture, doing stylish hip sway and synchronized rhythmic hand claps to the rhythm',
        'Phase 6 Final Convergence: The woman smoothly straightens both legs to full tall slender height, lowers both arms and places hands on hips, standing perfectly upright in her exact starting posture for a 100% seamless loop'
    ]
}

def plan_choreography(style='kpop', duration=20, bpm=120, char_lock_prompt=''):
    num_shots = max(1, duration // 5)
    pattern = CHOREO_PATTERNS.get(style, CHOREO_PATTERNS['kpop'])
    
    if num_shots == 4:
        # Standard 20s (4 shots): Intro -> Build-up -> Drop -> Convergence
        selected = [pattern[0], pattern[1], pattern[2], pattern[3]]
    elif num_shots == 6:
        # Standard 30s (6 shots): Intro -> Build-up -> Drop -> Groove -> Release -> Final Convergence
        selected = [pattern[0], pattern[1], pattern[2], pattern[4], pattern[2], pattern[5]]
    else:
        selected = []
        for i in range(num_shots - 1):
            selected.append(pattern[i % 3])
        selected.append(pattern[3])
    
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
    shots = plan_choreography(style='kpop', duration=20, bpm=120, char_lock_prompt='[LOCK]')
    for s in shots:
        print(f"Shot {s['shot_id']} (Loop={s['is_loop_closure']}): {s['action']}")
