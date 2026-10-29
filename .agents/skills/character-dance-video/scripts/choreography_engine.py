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
    '平视中景建立与起范': 'Phase 1 Spatial Establishing & Hip Anchoring: 35mm lens at chest level 110cm with natural f/2.2 shallow depth of field, slow linear dolly out, dancer hands resting gracefully against outer hip crests with fingers naturally curled and thumb slightly apart, executing pelvic tilt Bounce Down and Up-bounce cycle on 120 BPM beat with knees flexing 15 degrees, hair floating dynamically with bounce inertia, continuous direct eye contact with camera',
    '卡点仰角特写与翻掌开花': 'Phase 2 Low-Angle Close-Up & Palm Blossom: 85mm portrait telephoto lens at 90cm height with +15-degree low angle framing jawline and clavicle, hands executing palm blossom micro-action in front of chest as wrists rapidly rotate from facing inward to blooming outward with manicured fingertips fanning open in stepped curvature, sharp 3cm thoracic chest pop on the heavy beat with crisp dime stop and elastic rebound',
    '核心全景静止锁定与8字摆胯': 'Phase 3 Static Lock & Figure-8 Hip Roll: 28mm wide lens at 80cm navel height with +5-degree upward angle locked in absolute static framing without any visible camera equipment, tripod, or props in frame, pelvis tracing smooth continuous horizontal figure-8 double loops with deep hip roll displacement while thoracic spine executes counter-balance horizontal shift, hands lightly touching occipital hairline behind head with elbows flared 90 degrees, hair following head turns with 45-degree inertia lag phase and fan-like centrifugal flare',
    '双拳活塞顿点律动': 'Phase 4 Piston Punch Rhythmic Groove: 35mm golden frontal viewing angle, hands loosely balled into fists positioned on sides of upper abdomen, executing vertical 5cm piston-like downward snapping beats synchronized with foot bounces, hair strands demonstrating zero-G spring suspension when torso descends, confident engaging eye contact',
    '低角度纵深跟随推进': 'Phase 5 Low-Angle Dynamic Forward Tracking: 50mm natural perspective lens at 60cm knee height with +12-degree low angle tracking smoothly, dancer taking confident strides forward towards camera transitioning from medium shot into intimate close-up with intense presence, stable core groove and direct captivating gaze, strictly no turning away',
    '优雅减速定格闭环': 'Phase 6 Seamless Convergence & Loop Closure: during final 1.5 seconds, gradually decelerating all motion, dancer bringing whole body, posture, and arms smoothly down to sides, hair falling naturally across collarbone in gentle parabolic waves under gravity, gentle smiling expression holding steady, 100 percent pixel-faithful convergence into exact initial standing pose for flawless loop',
    '千金亮相卡点': 'Phase 1 Intro (K-Pop Idol Point): strictly frontal orientation facing camera directly throughout, eyes locked onto camera with confident radiant sweet smile, hands moving smoothly from starting pose down to sides, performing snappy rhythmic shoulder pops on 128 BPM beat, subtle waist groove, stationary feet, strictly no turning away',
    '名媛指尖框脸与S律动': 'Phase 2 Point Dance: staying strictly frontal facing camera directly, raising manicured fingertips gracefully to chin and cheek level, executing stylish K-Pop face-framing point gestures, executing fluid continuous S-curve waist isolations to the energetic rhythm, head nodding gently on beat with captivating gentle gaze, direct eye contact',
    '核心胸腔卡点与双臂展开': 'Phase 3 Chest Pops: strictly frontal orientation facing camera, hands resting naturally near hips, executing sharp snappy chest pops and fluid outward arm extensions, feet planted firmly in stationary position without turning, natural neck-body alignment, continuous eye contact',
    '高潮GirlCrush弹跳律动': 'Phase 4 Chorus Drop (Girl Crush Peak): high-energy frontal drop beat, dancing directly facing camera without turning, crossing arms stylishly in front of chest and pushing outward on the peak beat, executing energetic frontal hip sway and bouncy shoulder groove, staying stationary and strictly frontal without showing back',
    '灵动指尖点拍与肩部摇摆': 'Phase 5 Point Tap Groove: staying strictly frontal facing camera directly, one hand lightly touching hair near ear, other hand tapping rhythm in front of chest, executing agile rhythmic shoulder dips, sweet charming smile, direct eye contact with camera, outfit silhouette staying crisp and stable',
    '元气起手': 'facing camera with upright stationary posture, feet planted firmly in place, resting hands lightly at side hips, engaging in snappy rhythmic shoulder pops, natural sweet smile, subtle rhythmic bounce on beat, maintaining generous headroom above head',
    '核心S曲线快摇': 'facing camera with stationary upright posture, feet planted, hands resting lightly at side hips without covering torso, executing rapid fluid continuous S-curve hip sway and snappy waist isolations to the energetic beat, stationary tripod framing with generous headroom',
    '踏步核心律动': 'standing firmly anchored in place with feet planted without stepping forward or zooming in, delicate wrist isolations and subtle rhythmic hip sway to the beat, hands at side hips, strictly maintaining full distance from camera with generous headroom above head and whole head clearly visible',
    '胸腔波浪与核心律动': 'standing stationary with feet planted, performing fluid torso and chest rhythmic pulses to the climax beat while keeping hands down at hips, eye contact with camera, maintaining stationary tripod framing and generous headroom',
    '高潮快节奏摇摆': 'high-energy fast-paced hip sway and bouncy shoulder groove while standing firmly anchored in place, arms naturally at sides, sweet smile, staying stationary in the frame with generous headroom above head and intact clothing',
    '无缝闭环收尾': 'during the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, bringing her arms, posture, body alignment, and sweet smiling expression smoothly back into the exact original reference starting pose, holding perfectly steady on the final beat for a flawless seamless loop',
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

def plan_choreography(style='street', duration=30, bpm=120, char_lock_prompt='', template_id=None, is_rear_pose=False, is_kneeling_pose=False, is_indoor=False, custom_sequence_desc=None):
    num_shots = max(1, duration // 5)
    tpl_data = load_template_actions(template_id) if template_id else None
    
    if is_kneeling_pose:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, gracefully descending back down onto the floor and settling whole body and arms 100% into the exact original kneeling starting pose on knees with hand touching hair, perfectly holding and freezing steady on the final beat for a seamless loop"
    elif is_rear_pose:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, executing a coordinated natural full-body pivot and turn, gracefully settling whole body and torso 100% into the exact original 3/4 rear reference orientation with head looking back over shoulder, perfectly holding and freezing steady on the final beat for a seamless loop"
    else:
        convergence_action = "Phase Convergence (Seamless Loop Closure): During the final 1.5 seconds, the woman smoothly and gradually decelerates all dancing motion, bringing her arms, posture, body alignment, and facial expression 100% back into the exact original reference starting pose, holding perfectly steady on the final beat for a flawless seamless loop"
    
    # 优先分支 1: 用户自由编排自定义动作序列 (由前端自由编舞工作台传入)
    import re
    custom_steps = []
    if custom_sequence_desc and ("Sequence:" in custom_sequence_desc or "Shot " in custom_sequence_desc):
        seq_text = custom_sequence_desc.split("Sequence:", 1)[-1].strip() if "Sequence:" in custom_sequence_desc else custom_sequence_desc
        parts = [p.strip() for p in seq_text.split(";") if p.strip()]
        for p in parts:
            m = re.match(r'Shot\s*\d+\s*(?:\((.*?)\))?:\s*(.*)', p, re.IGNORECASE)
            if m:
                angle_tag = m.group(1) or "frontal"
                prompt_content = m.group(2).strip()
                custom_steps.append(f"Phase ({angle_tag} dynamic camera framing): {prompt_content}")
            else:
                custom_steps.append(p)
                
    if custom_steps:
        print(f"  [Choreography Engine] 🎯 Loaded Custom Choreography Sequence ({len(custom_steps)} user-curated poses)")
        selected = []
        if len(custom_steps) > 1:
            for step in custom_steps[:-1]:
                selected.append(step)
            # 最后一个动作融合收束闭环，确保最后一个定格动作不被冲掉
            last_step = custom_steps[-1]
            selected.append(f"{last_step}. Finishing transition: gracefully holding and freezing on the final beat for a seamless loop closure.")
        else:
            selected.append(custom_steps[0])
            selected.append(convergence_action)
    elif tpl_data and tpl_data.get('actions'):
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
                    act_text = core_actions[action_idx]
                    if not act_text.startswith("Phase"):
                        act_text = f"Phase {i+1} (Fast Energy): The woman executes fast-paced snappy {act_text}"
                    selected.append(act_text)
        
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
    shot_dur = max(3, int(round(duration / max(1, len(selected)))))
    for i, action in enumerate(selected):
        is_last = (i == len(selected) - 1)
        full_prompt = f'{char_lock_prompt} {action}'
        shots.append({
            'shot_id': i + 1,
            'is_loop_closure': is_last,
            'action': action,
            'prompt': full_prompt,
            'duration_sec': shot_dur
        })
    return shots

if __name__ == '__main__':
    shots = plan_choreography(style='street', duration=30, bpm=120, char_lock_prompt='[LOCK]', template_id='DANCE_THAI_SWAY')
    for s in shots:
        print(f"Shot {s['shot_id']} (Loop={s['is_loop_closure']}): {s['action']}")
