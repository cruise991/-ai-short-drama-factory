#!/usr/bin/env python3
import os
import re

ARCHETYPES = {
    'street': {
        'subject': 'A gorgeous 20-year-old East Asian Japanese woman with shoulder-length dark brown straight hair and wispy bangs, cheerful radiant smile and voluptuous curvy figure',
        'outfit': 'wearing a seamless one-piece grey and white micro-houndstooth textured sleeveless micro mini sundress with deep scoop neckline, flat smooth unembellished waistline with strictly NO belt, NO waist-tie, and NO elastic band, ultra-fine delicate micro-dot fabric texture, bare legs, and ankle-strap high heel sandals',
        'scene': 'outdoor traditional Japanese wooden town street background with rustic wooden houses, pavement road and warm sunny daytime lighting, consistent architecture',
        'style_keywords': ['street', 'town', 'japanese', 'houndstooth', 'sundress', 'wooden']
    },
    'kpop': {
        'subject': 'A gorgeous 20-year-old East Asian Korean female idol with styled dark hair, soft delicate facial features, bright sweet joyful smile',
        'outfit': 'wearing a fitted micro mini dress ending firmly at upper thighs, bare legs, and platform heels',
        'scene': 'pure minimalist dark stage background, subtle reflective floor, soft ambient rim lighting, no furniture, no rooms',
        'style_keywords': ['kpop', 'idol', 'stage']
    },
    'fitness': {
        'subject': 'A gorgeous 20-year-old East Asian athletic woman with long wavy dark brown hair, healthy glowing skin, radiant smile',
        'outfit': 'wearing a sports top and athletic compression leggings, bare legs or socks, and high heels',
        'scene': 'clean minimalist light grey photo studio background, soft studio diffused lighting',
        'style_keywords': ['fitness', 'gym', 'athletic', 'leggings', 'sports', 'bra']
    }
}

CAMERA_LOCK = 'Full body shot, head to toe completely visible in frame, ample headroom above head, shoes visible, ultra tall slender 9-head model proportions, straight fully extended long legs, upright erect posture, stable fixed camera angle'

def analyze_character_and_scene(image_path, user_desc=None, style_hint='street'):
    filename = os.path.basename(image_path).lower() if image_path else ''
    desc_lower = (user_desc or '').lower()
    
    # Detect Pose Orientation (Rear 3/4, Side, or Front)
    is_rear_pose = any(kw in desc_lower or kw in filename for kw in ['back', 'rear', 'shoulder', 'looking back', 'behind', 'backside', '3/4 rear'])
    if is_rear_pose:
        orientation_lock = 'Consistent 3/4 rear body orientation, back of outfit strictly facing camera, head gracefully turned looking back over shoulder with natural anatomical neck alignment, strictly NO front chest on back'
    else:
        orientation_lock = 'Consistent natural body orientation, upright posture, natural anatomical head-torso alignment'
    
    selected_style = 'street'
    if style_hint and style_hint in ARCHETYPES:
        selected_style = style_hint
    else:
        for style_key, data in ARCHETYPES.items():
            if any(kw in filename or kw in desc_lower for kw in data['style_keywords']):
                selected_style = style_key
                break
    base_meta = ARCHETYPES[selected_style]
    
    if user_desc:
        subject_layer = user_desc
        parts = [CAMERA_LOCK, orientation_lock, subject_layer, 'Exact same setting and 100% consistent character face, tall stature, identical clothing, accessories, and shoes across all frames']
    else:
        subject_layer = base_meta['subject']
        outfit_layer = base_meta['outfit']
        scene_layer = base_meta['scene']
        parts = [CAMERA_LOCK, orientation_lock, subject_layer, outfit_layer, f"Exact same {scene_layer}, 100% consistent lighting and background"]
        
    prompt_lock = '. '.join([p.strip() for p in parts if p.strip()]) + '.'
    prompt_lock = re.sub(r'\.+', '.', prompt_lock).strip()
    return {
        'style': selected_style,
        'camera_lock': CAMERA_LOCK,
        'subject_layer': subject_layer,
        'is_rear_pose': is_rear_pose,
        'full_prompt_lock': prompt_lock
    }

if __name__ == '__main__':
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
    meta = analyze_character_and_scene(test_img, style_hint='street')
    print(meta['full_prompt_lock'])
