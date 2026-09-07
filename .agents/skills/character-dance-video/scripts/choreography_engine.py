#!/usr/bin/env python3
import os
import json
import glob

def get_templates_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, '..', '..', '..', 'assets', 'dance', '07_templates'),
        os.path.join(script_dir, '..', '..', '..', '..', 'assets', 'dance', '07_templates'),
        '/Users/workspace/ai_short_company/ai-short-drama/assets/dance/07_templates',
        '/workspace/assets/dance/07_templates'
    ]
    for c in candidates:
        norm = os.path.abspath(c)
        if os.path.exists(norm):
            return norm
    return os.path.abspath(candidates[0])

TEMPLATES_DIR = get_templates_dir()

ACTION_TRANSLATIONS = {
    '元气起手': 'facing camera with upright stationary posture, feet planted firmly in place, resting hands lightly at side hips, engaging in snappy rhythmic shoulder pops, natural sweet smile, subtle rhythmic bounce on beat, maintaining generous headroom above head',
    '核心S曲线快摇': 'facing camera with stationary upright posture, feet planted, hands resting lightly at side hips without covering torso, executing rapid fluid continuous S-curve hip sway and snappy waist isolations to the energetic beat, stationary tripod framing with generous headroom',
    '踏步核心律动': 'standing firmly anchored in place with feet planted without stepping forward or zooming in, delicate wrist isolations and subtle rhythmic hip sway to the beat, hands at side hips, strictly maintaining full distance from camera with generous headroom above head and whole head clearly visible',
    '胸腔波浪与核心律动': 'standing stationary with feet planted, performing fluid torso and chest rhythmic pulses to the climax beat while keeping hands down at hips, eye contact with camera, maintaining stationary tripod framing and generous headroom',
    '高潮快节奏摇摆': 'high-energy fast-paced hip sway and bouncy shoulder groove while standing firmly anchored in place, arms naturally at sides, sweet smile, staying stationary in the frame with generous headroom above head and intact clothing',
    '无缝闭环收尾': 'during the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, bringing her arms, posture, and expression smoothly back into the exact original reference starting pose with right hand resting naturally near thigh, holding perfectly steady on the final beat for a flawless seamless loop',
    '亮相起手': 'facing camera with upright posture, extending arms gently to the sides, smiling sweetly into the camera with subtle rhythm bounce, hair strands fluttering in the gentle coastal breeze',
    '柔美S曲线律动': 'facing forward directly towards camera with direct sweet eye contact, executing fluid continuous S-curve hip sway and gentle waist isolations with natural upper body posture within anatomical range, soft hair fluttering in breeze',
    '胸腔波浪律动': 'facing forward with upright posture, executing fluid upper-body chest waves and smooth torso isolations, glancing down shyly then looking up smiling warmly into camera, natural kinetic bounce, soft hair fluttering in breeze',
    '轻盈踏步律动': 'performing light agile micro-steps in place facing forward without turning, gently touching hair strands with one hand, swaying hips gracefully to the upbeat rhythm within natural frontal alignment',
    '高潮核心摇摆': 'executing energetic frontal S-curve hip rolls and lively shoulder grooves to the peak beat with radiant sweet smile, natural kinetic bounce, maintaining upright posture without spinning or turning away',
    '减速定格收尾': 'gradually decelerating dance movement during the final 1.5 seconds, bringing hands and posture smoothly back into exact initial open-arm standing pose, holding steady with sweet smile for a flawless seamless loop',
    '预备': 'standing ultra tall with straight long legs, engaging in snappy rhythmic shoulder pops and stylish head bobbing to the fast beat',
    '起手': 'standing ultra tall, quickly raising hands in sharp stylish K-pop point dance pose, bouncing actively to the fast tempo',
    '起手式': 'standing tall with long straight legs, performing rapid stylish wrist isolations and energetic dynamic waist sway to the beat',
    '亮相': 'standing ultra tall with long legs, striking a cute charming face frame pose with graceful hands, bouncing rhythmically on beat',
    '跳跃段': 'doing energetic light bouncy dance hops, rhythmic arm arcs and rapid snappy hip groove on the high-energy drop',
    '手臂波浪': 'performing rapid fluid arm waves, snappy body wave isolations and active rhythmic step-touch footwork on beat',
    '灵魂摇摆': 'performing fast-paced dynamic hip sway, agile step-touch footwork and lively arm movements timed to the upbeat rhythm',
    '核心摇摆': 'executing rapid snappy hip roll, dynamic chest pops and fast rhythmic side-stepping with vibrant cheerful expression',
    '核心白菜摇': 'performing energetic rhythmic hand gestures, snappy body sway, dynamic hip roll and lively step touches to the upbeat rhythm',
    '挤柠檬': 'performing snappy downward hand groove isolations, fast torso body wave and rapid syncopated sliding footwork',
    '崴脚步核心': 'performing fast stylish foot sliding, rapid snappy ankle groove and dynamic hip wave isolations on fast beat',
    '丝滑手部': 'performing fast fluid wrist rotations, sharp finger gestures, and energetic continuous body wave to the rhythm',
    '全身波浪': 'performing snappy full body wave, rapid 180-degree stylish turn with natural coordinated head-torso rotation as one anatomical unit keeping head and shoulders aligned, fast-paced agile footwork',
    '加速': 'doing fast-paced high-energy bouncing steps, rapid hip snaps, and cheerful radiant expression to the fast tempo',
    '加速段': 'executing rapid snappy choreography, high-speed arm gestures, and lively energetic body bounce',
    '变奏': 'performing snappy stylish spin, agile body wave and rapid rhythmic step isolations while maintaining full upright height',
    '变奏加速': 'executing fast bouncy rhythmic footwork, dynamic hip snaps and rapid energetic body groove on the drop',
    '交叉挥动': 'executing rapid sharp arm crosses and snappy outward swings, fast syncopated foot sliding and energetic body groove',
    '旋转': 'executing graceful controlled 360-degree stylish spin with fluid arm extensions while maintaining natural coordinated head-torso alignment throughout the entire spin, head and shoulders rotating together as one natural anatomical unit, tall erect posture',
    '转身': 'doing rapid stylish half-spin with natural coordinated head-body rotation, head and torso turning together smoothly as one anatomically correct unit, snappy body groove with sweet radiant smile',
    '展翅': 'gracefully extending both arms wide, lifting torso tall and swaying rhythmically to the melody',
    '天使降临': 'standing tall and poised, performing gentle ethereal shoulder groove and soft graceful hand gestures',
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

def plan_choreography(style='street', duration=30, bpm=120, char_lock_prompt='', template_id=None, is_rear_pose=False, is_kneeling_pose=False, is_indoor=False):
    num_shots = max(1, duration // 5)
    tpl_data = load_template_actions(template_id) if template_id else None
    
    if is_kneeling_pose:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, gracefully descending back down onto the floor and settling whole body and arms 100% into the exact original kneeling starting pose on knees with hand touching hair, perfectly holding and freezing steady on the final beat for a seamless loop"
    elif is_rear_pose:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, executing a coordinated natural full-body pivot and turn, gracefully settling whole body and torso 100% into the exact original 3/4 rear reference orientation with head looking back over shoulder, perfectly holding and freezing steady on the final beat for a seamless loop"
    else:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, bringing her arms, posture, body alignment, and facial expression 100% back into the exact original reference starting pose, holding perfectly steady on the final beat for a flawless seamless loop"
    
    if tpl_data and tpl_data.get('actions'):
        raw_actions = tpl_data['actions']
        print(f"  [Choreography Engine] Loaded Dance Template: {tpl_data['name']} ({len(raw_actions)} key steps)")
        selected = []
        core_actions = raw_actions[:-1] if len(raw_actions) > 1 else raw_actions
        for i in range(num_shots - 1):
            action_idx = i % len(core_actions)
            if is_kneeling_pose and i == 0:
                selected.append("Phase 1 Intro (Kneeling Floor Groove): The woman begins in her charming kneeling floor pose on knees, performing fluid upper body torso waves, stylish shoulder pops and graceful hand gestures to the upbeat beat")
            elif is_kneeling_pose and i == 1:
                selected.append("Phase 2 Rising Momentum: The woman smoothly and gracefully rises from kneeling up to her full ultra-tall standing height revealing extremely long slender legs, 9-head supermodel proportions where legs occupy at least 55 percent of total body height, willowy tall figure with fully extended straight knees, transitioning actively into energetic bouncy dance steps on beat")
            else:
                if is_kneeling_pose and i >= 2:
                    selected.append(f"Phase {i+1} (Fast Energy): The woman, now standing at her full ultra-tall 9-head supermodel height with extremely long straight legs, executes fast-paced snappy {core_actions[action_idx]}")
                else:
                    selected.append(f"Phase {i+1} (Fast Energy): The woman executes fast-paced snappy {core_actions[action_idx]}")
        
        # Final closure step
        selected.append(convergence_action)
    else:
        # Default high-energy fast-paced choreography pattern
        patterns = [
            'Phase 1 Intro (Fast Beat): The woman maintains an ultra-tall posture with straight long legs, beginning fast-paced snappy rhythmic groove, rapid hip pops on beat with radiant smile',
            'Phase 2 Build-up (High Tempo): The woman executes snappy dynamic body sway, doing fast stylish hip rolls and fluid quick arm waves timed with the rapid beat',
            'Phase 3 Chorus Drop (Fast Energy): The woman grooves with high-speed bouncy rhythm, doing snappy wrist rotations, fast agile sliding steps to the upbeat tempo',
            'Phase 4 Climax (Peak Rhythm): The woman continues energetic fast rhythmic dance with long legs, performing dynamic torso waves and sharp stylish arm gestures',
            'Phase 5 Rhythm Release (Fast Footwork): The woman steps rapidly in place with snappy agile footwork, stylish body groove and cheerful confident gaze',
            convergence_action
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
