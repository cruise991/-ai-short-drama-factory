#!/usr/bin/env python3
import os
import re

ARCHETYPES = {
    'fitness': {
        'subject': 'A gorgeous 20-year-old East Asian athletic woman with long wavy dark brown hair, soft youthful sweet features, radiant smile',
        'outfit': 'wearing a black and red sports crop top bra, high-waisted white compression athletic leggings, black over-the-knee high socks, and red high heel shoes',
        'scene': 'clean minimalist light grey photo studio background, soft studio diffused lighting, solid neutral color palette',
        'style_keywords': ['fitness', 'gym', 'athletic', 'leggings', 'sports', 'bra', 'workout']
    },
    'street': {
        'subject': 'A stylish 20-year-old East Asian young woman with long dark wavy hair, delicate natural facial features, smiling charmingly',
        'outfit': 'wearing a black sleeveless turtleneck crop top, a high-waisted white asymmetrical slit midi skirt, gold necklace, and silver high heel pumps',
        'scene': 'outdoor modern city street background with high-rise buildings and sunny daytime lighting, consistent urban architecture',
        'style_keywords': ['street', 'city', 'urban', 'skirt', 'slit', 'outdoor']
    },
    'kpop': {
        'subject': 'A charming 20-year-old East Asian Korean female idol with long styled dark hair, soft delicate facial features, bright sweet joyful smile',
        'outfit': 'wearing a white sleeveless micro mini dress ending firmly at upper thighs with side pleated detail, legs fully visible, and platform peep-toe heels',
        'scene': 'pure minimalist dark stage background, subtle reflective floor, soft ambient rim lighting, no furniture, no rooms',
        'style_keywords': ['kpop', 'idol', 'whitedress', 'mini dress', 'stage', 'dark stage']
    },
    'luxury': {
        'subject': 'An elegant 20-year-old East Asian woman with soft delicate features, styled long dark wavy hair, poised sweet smile',
        'outfit': 'wearing a white sleeveless micro mini dress ending at upper thighs, legs fully visible, and high heel platform pumps',
        'scene': 'pure dark minimalist studio stage background with soft floor reflection, no furniture, no walls',
        'style_keywords': ['luxury', 'glamour', 'dress', 'cocktail']
    }
}

CAMERA_LOCK = 'Full body shot, head to toe completely visible in frame, ample headroom above head, shoes visible, centered composition, stable fixed camera angle'

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
    
    # If user provides description, 100% honor user input and DO NOT append conflicting archetype scenes
    if user_desc:
        subject_layer = user_desc
        scene_layer = ''
        outfit_layer = ''
        parts = [CAMERA_LOCK, subject_layer, 'Exact same setting and 100% consistent character face and clothing length across all frames']
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
        'outfit_layer': outfit_layer,
        'scene_layer': scene_layer,
        'full_prompt_lock': prompt_lock
    }

if __name__ == '__main__':
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
    meta = analyze_character_and_scene(test_img, style_hint='kpop')
    print(meta['full_prompt_lock'])
