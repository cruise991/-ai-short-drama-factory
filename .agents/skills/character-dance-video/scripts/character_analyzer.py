#!/usr/bin/env python3
import os
import re

ARCHETYPES = {
    'kpop': {
        'subject': 'A gorgeous 20-year-old East Asian Korean female idol with short dark brown bob hair, soft delicate facial features, bright sweet joyful smile',
        'outfit': 'wearing a white spaghetti-strap tank top, a high-waisted bright yellow pleated micro mini tennis skirt ending firmly at upper thighs, bare legs, and yellow high heel pumps',
        'scene': 'pure minimalist dark stage background, subtle reflective floor, soft ambient rim lighting, no furniture, no rooms',
        'style_keywords': ['kpop', 'idol', 'yellow skirt', 'mini skirt', 'tennis skirt', 'stage']
    },
    'fitness': {
        'subject': 'A gorgeous 20-year-old East Asian athletic woman with long wavy dark brown hair, soft youthful sweet features, radiant smile',
        'outfit': 'wearing a sports top and athletic compression leggings, bare legs or socks, and high heels',
        'scene': 'clean minimalist light grey photo studio background, soft studio diffused lighting, solid neutral color palette',
        'style_keywords': ['fitness', 'gym', 'athletic', 'leggings', 'sports', 'bra']
    }
}

CAMERA_LOCK = 'Full body shot, head to toe completely visible in frame, ample headroom above head, shoes visible, ultra tall slender 9-head model proportions, straight fully extended long legs, upright erect posture, stable fixed camera angle'

def analyze_character_and_scene(image_path, user_desc=None, style_hint='kpop'):
    filename = os.path.basename(image_path).lower() if image_path else ''
    desc_lower = (user_desc or '').lower()
    
    selected_style = 'kpop'
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
        parts = [CAMERA_LOCK, subject_layer, 'Exact same setting and 100% consistent character face, tall stature, and clothing length across all frames']
    else:
        subject_layer = base_meta['subject']
        outfit_layer = base_meta['outfit']
        scene_layer = base_meta['scene']
        parts = [CAMERA_LOCK, subject_layer, outfit_layer, f"Exact same {scene_layer}, 100% consistent lighting and background"]
        
    prompt_lock = '. '.join([p.strip() for p in parts if p.strip()]) + '.'
    prompt_lock = re.sub(r'\.+', '.', prompt_lock).strip()
    return {
        'style': selected_style,
        'camera_lock': CAMERA_LOCK,
        'subject_layer': subject_layer,
        'full_prompt_lock': prompt_lock
    }

if __name__ == '__main__':
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
    meta = analyze_character_and_scene(test_img, style_hint='kpop')
    print(meta['full_prompt_lock'])
