#!/usr/bin/env python3
import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'assets', 'dance', '07_templates')

ACTION_TRANSLATIONS = {
    '预备': 'standing ultra tall and poised with fully extended long legs, subtle rhythmic shoulder groove',
    '起手': 'standing ultra tall, raising hands gracefully to chest level and swaying rhythmically on beat',
    '起手式': 'standing perfectly erect with long legs, doing subtle head groove and wrist rotation',
    '灵魂摇摆': 'smooth rhythmic side-to-side hip sway, body wave, and gentle arm arcs while keeping tall posture',
    '核心摇摆': 'dynamic rhythmic hip groove and stylish arm gestures, swaying gently to the beat with bright smile',
    '挤柠檬': 'stylish downward hand groove, body wave, rhythmic side-stepping with straight legs',
    '崴脚步核心': 'stylish rhythmic sliding footwork, smooth side-to-side body groove with tall posture',
    '丝滑手部': 'fluid wrist rotations and graceful arm wave isolations on beat',
    '加速': 'energetic rhythmic hip sway, bouncing step-touch and cheerful smile timed to the beat',
    '加速段': 'faster upbeat body groove, snappy arm movements and cheerful radiant expression',
    '变奏': 'stylish 360-degree slow spin and graceful body wave while maintaining full height',
    '变奏加速': 'bouncy rhythmic dance steps, dynamic hand claps and waist sway on the drop',
    '定格': 'smoothly straightening both legs, lowering arms naturally to sides or waist, standing perfectly upright for a seamless loop',
    '收尾': 'smoothly straightening both legs, lowering arms naturally to sides, standing perfectly upright in starting pose for a seamless loop'
}

def load_template_actions(template_name_or_id):
    if not template_name_or_id:
        return None
    
    target_path = None
    if os.path.exists(template_name_or_id):
        target_path = template_name_or_id
    else:
        cand1 = os.path.join(TEMPLATES_DIR, f"{template_name_or_id}.json")
        cand2 = os.path.join(TEMPLATES_DIR, f"DANCE_{template_name_or_id.upper()}.json")
        if os.path.exists(cand1): target_path = cand1
        elif os.path.exists(cand2): target_path = cand2
        else:
            # Fuzzy search in templates
            for f in glob.glob(os.path.join(TEMPLATES_DIR, '*.json')):
                if template_name_or_id.lower() in os.path.basename(f).lower():
                    target_path = f
                    break
    
    if not target_path or not os.path.exists(target_path):
        return None
        
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            timeline = data.get('timeline', [])
            actions = []
            for item in timeline:
                name = item.get('name', '')
                desc = item.get('action_prompt', '')
                translated = ACTION_TRANSLATIONS.get(name, f"{desc}, keeping ultra-tall slender posture")
                actions.append(translated)
            raw_bpm = data.get('bpm', '120')
            bpm = int(str(raw_bpm).split('-')[0].strip()) if '-' in str(raw_bpm) else (int(raw_bpm) if str(raw_bpm).isdigit() else 120)
            return {'actions': actions, 'bpm': bpm, 'name': data.get('name', 'Template')}
    except Exception as e:
        print(f"[Choreography Engine] Template load error: {e}")
        return None

def plan_choreography(style='street', duration=30, bpm=120, char_lock_prompt='', template_id=None):
    num_shots = max(1, duration // 5)
    tpl_data = load_template_actions(template_id) if template_id else None
    
    if tpl_data and tpl_data.get('actions'):
        raw_actions = tpl_data['actions']
        print(f"  [Choreography Engine] Loaded Dance Template: {tpl_data['name']} ({len(raw_actions)} key steps)")
        selected = []
        for i in range(num_shots - 1):
            action_idx = min(i, len(raw_actions) - 2) if len(raw_actions) > 2 else 0
            selected.append(f"Phase {i+1}: The woman standing ultra tall with long legs, performs {raw_actions[action_idx]}")
        
        # Final closure step
        selected.append("Phase Convergence: The woman smoothly straightens both legs to full tall height, lowers arms naturally to sides or hips, turning straight forward to settle 100% into her exact original starting posture for a seamless loop")
    else:
        # Default high-robustness choreography pattern
        patterns = [
            'Phase 1 Intro: The woman maintains an ultra-tall erect posture with straight long legs, beginning gentle rhythmic groove, swaying hips side-to-side on beat with sweet radiant smile',
            'Phase 2 Build-up: The woman executes graceful body sway with straight tall posture, doing stylish hip roll and gentle arm waves timed with the upbeat rhythm',
            'Phase 3 Chorus Drop: The woman grooves with bouncy rhythm, doing stylish wrist rotations, light sliding steps, and cheerful head tilt to the beat',
            'Phase 4 Climax: The woman continues stylish rhythmic dance with long extended legs, performing smooth torso twist and elegant arm arcs',
            'Phase 5 Rhythm Release: The woman steps smoothly in place, doing synchronized rhythmic hand claps and cheerful smiling gaze',
            'Phase 6 Final Convergence: The woman smoothly straightens both legs to full tall slender height, lowers both arms gracefully to sides, turning straight forward to settle 100% into her exact original starting posture for a seamless loop'
        ]
        if num_shots <= len(patterns):
            selected = patterns[:num_shots - 1] + [patterns[-1]]
        else:
            selected = [patterns[i % (len(patterns) - 1)] for i in range(num_shots - 1)] + [patterns[-1]]

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
    shots = plan_choreography(style='street', duration=30, bpm=120, char_lock_prompt='[LOCK]', template_id='DANCE_THAI_SWAY')
    for s in shots:
        print(f"Shot {s['shot_id']} (Loop={s['is_loop_closure']}): {s['action']}")
