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

CAMERA_LOCK = 'Full body master wide shot, head to toe completely visible with generous headroom above head and shoes fully framed, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, ultra-tall slender 9-head supermodel proportions with straight fully extended long legs and upright erect posture'
CAMERA_LOCK_MODERATE = 'Full body master wide shot, head to toe completely visible with moderate headroom (approximately 10 percent of frame height) above head, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, ultra-tall slender 9-head supermodel proportions with straight fully extended long legs occupying at least 55 percent of total body height and upright erect posture'

CAMERA_LOCK_MEDIUM_FULL = 'Medium-full shot framed from mid-thigh up, slightly high-angle 15-degree downward tripod perspective overlooking the beach, head and upper torso with beautiful collarbone and waist curves fully framed with moderate headroom, soft coastal ocean breeze physics with fluttering hair strands, strictly no random shoes on sand, barefoot or natural sand framing, graceful upright posture'

CAMERA_LOCK_STANDING_AFTER_KNEELING = 'Full body master wide shot, head to toe completely visible with moderate headroom (approximately 10 percent of frame height) above head and shoes fully framed, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, ultra-tall slender willowy 9-head supermodel proportions with extremely long straight legs occupying at least 55 percent of total body height, fully extended knees, upright erect posture'

FACE_LOCK = 'Strictly 100% consistent gorgeous East Asian face, soft youthful facial contours, natural round feminine jawline, delicate soft feminine facial features, dark almond eyes, radiant sweet charming smile, smooth porcelain skin, identical East Asian ethnicity and facial identity across all shots'

def analyze_character_and_scene(image_path, user_desc=None, style_hint='street'):
    filename = os.path.basename(image_path).lower() if image_path else ''
    desc_lower = (user_desc or '').lower()
    
    # Detect Pose Type (Kneeling/Floor, Rear 3/4, or Standard Standing Front)
    kneeling_patterns = [
        r'\bkneeling\b', r'\bkneel\b', r'\bon her knees\b', r'\bon his knees\b',
        r'\bfloor pose\b', r'\bsitting on knees\b', r'\bground pose\b', r'\b跪\b'
    ]
    is_kneeling_pose = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in kneeling_patterns)
    
    # Detect Pose Orientation (Rear 3/4, Side, or Front) with precise phrase matching to avoid matching 'background' or 'backdrop'
    rear_patterns = [
        r'\bback view\b', r'\brear view\b', r'\blooking back\b', r'\bfrom behind\b',
        r'\b3/4 rear\b', r'\bbackside\b', r'\brear pose\b', r'\bover her shoulder\b', r'\bover his shoulder\b'
    ]
    is_rear_pose = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in rear_patterns)
    
    medium_full_patterns = [
        r'\bthigh-up\b', r'\bmid-thigh\b', r'\bmedium-full\b', r'\bmedium shot\b',
        r'\bbikini\b', r'\bswimsuit\b', r'\bswimwear\b', r'\bbeach\b', r'\bbarefoot\b'
    ]
    is_medium_full = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in medium_full_patterns) and not any(re.search(p, desc_lower) for p in [r'\bshoes\b', r'\bboots\b', r'\bsneakers\b', r'\bheels\b', r'\bhead to toe\b'])

    if is_kneeling_pose:
        camera_lock = 'Full body master wide shot, head to knees and floor completely visible with moderate headroom above head, stable eye-level tripod camera, camera never tilts down, strictly no partial close-up, slender athletic model proportions'
        orientation_lock = 'Charming graceful kneeling floor pose on knees, hand gracefully touching hair, natural anatomical alignment'
    elif is_rear_pose:
        camera_lock = CAMERA_LOCK_MODERATE
        orientation_lock = 'Consistent 3/4 rear body orientation, back of outfit strictly facing camera, head gracefully turned looking back over shoulder with natural anatomical neck alignment, strictly NO front chest on back'
    elif is_medium_full:
        camera_lock = CAMERA_LOCK_MEDIUM_FULL
        orientation_lock = 'Consistent natural body orientation, upright posture, natural anatomical head-torso alignment'
    else:
        camera_lock = CAMERA_LOCK_MODERATE
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
        parts = [camera_lock, FACE_LOCK, orientation_lock, subject_layer, 'Exact same setting and 100% consistent character face, slender model proportions, identical clothing, accessories, and shoes across all frames']
    else:
        subject_layer = base_meta['subject']
        outfit_layer = base_meta['outfit']
        scene_layer = base_meta['scene']
        parts = [camera_lock, FACE_LOCK, orientation_lock, subject_layer, outfit_layer, f"Exact same {scene_layer}, 100% consistent lighting and background"]
        
    prompt_lock = '. '.join([p.strip() for p in parts if p.strip()]) + '.'
    prompt_lock = re.sub(r'\.+', '.', prompt_lock).strip()
    return {
        'style': selected_style,
        'camera_lock': camera_lock,
        'subject_layer': subject_layer,
        'is_rear_pose': is_rear_pose,
        'is_kneeling_pose': is_kneeling_pose,
        'full_prompt_lock': prompt_lock
    }

if __name__ == '__main__':
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
    meta = analyze_character_and_scene(test_img, style_hint='street')
    print(meta['full_prompt_lock'])
