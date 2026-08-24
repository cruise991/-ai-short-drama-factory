#!/usr/bin/env python3
import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'assets', 'dance', '07_templates')

ACTION_TRANSLATIONS = {
    '预备': 'standing ultra tall with straight long legs, engaging in snappy rhythmic shoulder pops and stylish head bobbing to the fast beat',
    '起手': 'standing ultra tall, quickly raising hands in sharp stylish K-pop point dance pose, bouncing actively to the fast tempo',
    '起手式': 'standing tall with long straight legs, performing rapid stylish wrist isolations and energetic dynamic waist sway to the beat',
    '跳跃段': 'doing energetic light bouncy dance hops, rhythmic arm arcs and rapid snappy hip groove on the high-energy drop',
    '手臂波浪': 'performing rapid fluid arm waves, snappy body wave isolations and active rhythmic step-touch footwork on beat',
    '灵魂摇摆': 'performing fast-paced dynamic hip sway, agile step-touch footwork and lively arm movements timed to the upbeat rhythm',
    '核心摇摆': 'executing rapid snappy hip roll, dynamic chest pops and fast rhythmic side-stepping with vibrant cheerful expression',
    '挤柠檬': 'performing snappy downward hand groove isolations, fast torso body wave and rapid syncopated sliding footwork',
    '崴脚步核心': 'performing fast stylish foot sliding, rapid snappy ankle groove and dynamic hip wave isolations on fast beat',
    '丝滑手部': 'performing fast fluid wrist rotations, sharp finger gestures, and energetic continuous body wave to the rhythm',
    '全身波浪': 'performing snappy full body wave, rapid 180-degree stylish turn and fast-paced agile footwork',
    '加速': 'doing fast-paced high-energy bouncing steps, rapid hip snaps, and cheerful radiant expression to the fast tempo',
    '加速段': 'executing rapid snappy choreography, high-speed arm gestures, and lively energetic body bounce',
    '变奏': 'performing snappy stylish spin, agile body wave and rapid rhythmic step isolations while maintaining full upright height',
    '变奏加速': 'executing fast bouncy rhythmic footwork, dynamic hip snaps and rapid energetic body groove on the drop',
    '交叉挥动': 'executing rapid sharp arm crosses and snappy outward swings, fast syncopated foot sliding and energetic body groove',
    '定格': 'smoothly straightening both legs to full tall height, lowering arms naturally to sides, standing upright into exact starting pose for a seamless loop',
    '收尾': 'smoothly straightening both legs to full tall height, lowering arms naturally to sides, standing upright into exact starting pose for a seamless loop',
    '收尾定格': 'smoothly straightening both legs to full tall height, lowering arms naturally to sides, standing upright into exact starting pose for a seamless loop'
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
        core_actions = raw_actions[:-1] if len(raw_actions) > 1 else raw_actions
        for i in range(num_shots - 1):
            action_idx = i % len(core_actions)
            selected.append(f"Phase {i+1} (Fast Energy): The woman standing ultra tall with long slender legs, executes fast-paced snappy {core_actions[action_idx]}")
        
        # Final closure step
        selected.append("Phase Convergence: The woman smoothly straightens both legs to full tall height, lowers arms naturally to sides, turning straight forward to settle 100% into her exact original starting posture for a seamless loop")
    else:
        # Default high-energy fast-paced choreography pattern
        patterns = [
            'Phase 1 Intro (Fast Beat): The woman maintains an ultra-tall posture with straight long legs, beginning fast-paced snappy rhythmic groove, rapid hip pops on beat with radiant smile',
            'Phase 2 Build-up (High Tempo): The woman executes snappy dynamic body sway, doing fast stylish hip rolls and fluid quick arm waves timed with the rapid beat',
            'Phase 3 Chorus Drop (Fast Energy): The woman grooves with high-speed bouncy rhythm, doing snappy wrist rotations, fast agile sliding steps to the upbeat tempo',
            'Phase 4 Climax (Peak Rhythm): The woman continues energetic fast rhythmic dance with long legs, performing dynamic torso waves and sharp stylish arm gestures',
            'Phase 5 Rhythm Release (Fast Footwork): The woman steps rapidly in place with snappy agile footwork, stylish body groove and cheerful confident gaze',
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
