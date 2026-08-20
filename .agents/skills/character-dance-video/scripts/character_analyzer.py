#!/usr/bin/env python3
import os
import re

ARCHETYPES = {
    'fitness': {
        'subject': 'A beautiful fit young athletic woman with long wavy dark brown hair, healthy glowing skin, energetic confident expression',
        'outfit': 'wearing a black and red sports crop top bra, high-waisted white compression athletic leggings, black over-the-knee high socks, and red high heel shoes',
        'scene': 'clean minimalist light grey photo studio background, soft studio diffused lighting, solid neutral color palette',
        'style_keywords': ['fitness', 'gym', 'athletic', 'leggings', 'sports', 'bra', 'workout']
    },
    'street': {
        'subject': 'A stylish young Korean woman with long dark wavy hair, delicate features, smiling charmingly',
        'outfit': 'wearing a black sleeveless turtleneck crop top, a high-waisted white asymmetrical slit midi skirt, gold necklace, and silver high heel pumps',
        'scene': 'outdoor modern city street background with high-rise buildings and sunny daytime lighting, consistent urban architecture',
        'style_keywords': ['street', 'city', 'urban', 'skirt', 'slit', 'outdoor']
    },
    'kpop': {
        'subject': 'A charming K-pop female idol with shoulder-length styled dark hair, bright cheerful joyful smile',
        'outfit': 'wearing a stylish crop top and a pleated mini skirt with matching platform sneakers and white socks',
        'scene': 'bright modern K-pop dance studio setting, clean glossy floor, warm accent lighting',
        'style_keywords': ['kpop', 'idol', 'stage', 'dance studio', 'pleated']
    },
    'luxury': {
        'subject': 'An elegant glamorous young woman with sophisticated makeup and styled hair, poised and graceful',
        'outfit': 'wearing a chic evening cocktail dress with high-end designer accessories and heels',
        'scene': 'luxurious modern indoor lounge setting with ambient architectural lighting',
        'style_keywords': ['luxury', 'glamour', 'dress', 'lounge', 'cocktail']
    }
}

CAMERA_LOCK = 'Full body shot, head to toe completely visible in frame, ample headroom above head, shoes visible, centered composition, stable fixed camera angle'

def analyze_character_and_scene(image_path, user_desc=None, style_hint='fitness'):
    filename = os.path.basename(image_path).lower() if image_path else ''
    desc_lower = (user_desc or '').lower()
    selected_style = 'fitness'
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
        outfit_layer = ''
        scene_layer = base_meta['scene']
    else:
        subject_layer = base_meta['subject']
        outfit_layer = base_meta['outfit']
        scene_layer = base_meta['scene']
    parts = [CAMERA_LOCK, subject_layer, outfit_layer, f'Exact same {scene_layer}, 100% consistent lighting and background']
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
    meta = analyze_character_and_scene(test_img, style_hint='fitness')
    print(meta['full_prompt_lock'])
