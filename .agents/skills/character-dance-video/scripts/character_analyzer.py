#!/usr/bin/env python3
import os
import sys
import re
import json
import urllib.request
import urllib.parse

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

CAMERA_LOCK = 'Full body master wide shot, head to toe completely visible with generous headroom above head and shoes fully framed, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, tall elegant 9-head model proportions with straight fully extended long legs and upright erect posture'
CAMERA_LOCK_MODERATE = 'Full body master wide shot, head to toe completely visible with moderate headroom (approximately 10 percent of frame height) above head, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, tall elegant 9-head model proportions with straight fully extended long legs occupying at least 55 percent of total body height and upright erect posture'

CAMERA_LOCK_MEDIUM_FULL = 'Medium-full shot framed from mid-thigh up, stable eye-level stationary tripod camera, camera never tilts down, head and upper torso fully framed with comfortable headroom, strictly no lower-body close-up, graceful feminine upright posture'

CAMERA_LOCK_INDOOR = 'Master medium-full shot framed from mid-thigh up, stable eye-level stationary tripod camera locked off at fixed focal distance, camera strictly prohibited from zooming in or tilting, generous headroom (at least 15 percent of frame height) above head, entire head completely visible in every frame, strictly no close-up, graceful feminine proportions with upright erect posture'

CAMERA_LOCK_STANDING_AFTER_KNEELING = 'Full body master wide shot, head to toe completely visible with moderate headroom (approximately 10 percent of frame height) above head and shoes fully framed, stable eye-level tripod camera, camera never tilts down, strictly no lower-body close-up, ultra-tall elegant 9-head model proportions with extremely long straight legs occupying at least 55 percent of total body height, fully extended knees, upright erect posture'

FACE_LOCK = 'Strictly 100% consistent character facial features, youthful soft gentle facial contours, soft natural jawline, delicate feminine facial features, natural captivating eyes, natural sweet closed-lip smile, perfectly even skin tone without blush, identical ethnicity and facial identity across all shots'

KINEMATIC_SAFETY = 'Strict human biomechanical constraints: head and torso must rotate together as a coordinated natural unit within anatomical cervical spine range (maximum 80 degrees neck rotation relative to shoulders). Shoulders, spine, and hips must maintain natural skeletal alignment throughout all dance movements. No disconnected or independent head-body rotation. No head facing opposite direction of chest. Smooth continuous natural joint articulation preserving anatomical plausibility in every frame'

def _load_env_if_needed():
    if not os.getenv("AGNES_API_KEY") and not os.getenv("AGNES_API_KEY_1"):
        possible_paths = [
            os.path.join(os.getcwd(), '.env'),
            os.path.join(os.getcwd(), 'ai-short-drama', '.env'),
            '/Users/workspace/ai_short_company/ai-short-drama/.env',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env')
        ]
        for p in possible_paths:
            if os.path.exists(p):
                with open(p) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            os.environ[k.strip()] = v.strip()
                break

def vision_describe_character(image_url):
    """Use Agnes 2.5 Flash Vision API to extract granular facial, body, outfit and scene features."""
    _load_env_if_needed()
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip('/')
    api_key = os.getenv("AGNES_API_KEY")
    if not api_key:
        for k in ['AGNES_API_KEY_1', 'AGNES_API_KEY_2', 'AGNES_API_KEY_3', 'AGNES_API_KEY_4', 'AGNES_API_KEY_5']:
            if os.getenv(k):
                api_key = os.getenv(k)
                break
    if not api_key or not image_url:
        return None

    prompt = (
        "Analyze this character reference image in extreme detail for video generation consistency. "
        "Return a valid JSON object with exactly these 4 keys:\n"
        "1. 'face': Specific facial contours, eye shape, visible double eyelids, aegyo-sal, nose bridge, lip shape, natural East Asian ethnicity features, smooth skin texture, gentle pleasant expression.\n"
        "2. 'body_type': Visible physical build and silhouette. CRITICAL: If the subject is voluptuous, curvy, or has a full rounded bust, explicitly describe 'full rounded bust, feminine curvy hourglass figure' - never generalize to skinny or flat.\n"
        "3. 'outfit': Precise clothing details including garment color, pattern, neckline, sleeve length, exact hemline/skirt length (e.g. 'fitted micro mini skirt ending at mid-thigh'), and footwear.\n"
        "4. 'scene': Background environment, furniture, and lighting.\n\n"
        "Output JSON only, no markdown formatting."
    )

    data = {
        "model": "agnes-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for model_name in ["agnes-2.5-flash", "agnes-2.0-flash"]:
        data["model"] = model_name
        req_body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/chat/completions", data=req_body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                raw_text = result["choices"][0]["message"]["content"].strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                    raw_text = re.sub(r"```\s*$", "", raw_text).strip()
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and ("face" in parsed or "body_type" in parsed):
                    print(f"  [Vision Analyzer] Successfully extracted character features via {model_name}")
                    return parsed
        except Exception as e:
            print(f"  [Vision Analyzer Warning] {model_name} failed: {e}")
            continue

    return None

def analyze_character_and_scene(image_path, user_desc=None, style_hint='street', image_url=None):
    filename = os.path.basename(image_path).lower() if image_path else ''
    desc_lower = (user_desc or '').lower()
    
    # Detect Pose Type (Kneeling/Floor, Rear 3/4, or Standard Standing Front)
    kneeling_patterns = [
        r'\bkneeling\b', r'\bkneel\b', r'\bon her knees\b', r'\bon his knees\b',
        r'\bfloor pose\b', r'\bsitting on knees\b', r'\bground pose\b', r'\b跪\b'
    ]
    is_kneeling_pose = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in kneeling_patterns)
    
    # Detect Pose Orientation (Rear 3/4, Side, or Front)
    rear_patterns = [
        r'\bback view\b', r'\brear view\b', r'\blooking back\b', r'\bfrom behind\b',
        r'\b3/4 rear\b', r'\bbackside\b', r'\brear pose\b', r'\bover her shoulder\b', r'\bover his shoulder\b'
    ]
    is_rear_pose = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in rear_patterns)
    
    indoor_patterns = [
        r'\bindoor\b', r'\bliving room\b', r'\bsofa\b', r'\bcouch\b', r'\broom\b', r'\bhome\b'
    ]
    is_indoor = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in indoor_patterns)

    caucasian_patterns = [
        r'\bcaucasian\b', r'\bwestern\b', r'\beuropean\b', r'\bamerican\b', r'\blatina\b', r'\bblonde\b'
    ]
    is_caucasian = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in caucasian_patterns)

    medium_full_patterns = [
        r'\bthigh-up\b', r'\bmid-thigh\b', r'\bmedium-full\b', r'\bmedium shot\b',
        r'\bbikini\b', r'\bswimsuit\b', r'\bswimwear\b', r'\bbeach\b', r'\bbarefoot\b'
    ]
    is_medium_full = any(re.search(pat, desc_lower) or re.search(pat, filename) for pat in medium_full_patterns) and not any(re.search(p, desc_lower) for p in [r'\bshoes\b', r'\bboots\b', r'\bsneakers\b', r'\bheels\b', r'\bhead to toe\b'])

    if is_kneeling_pose:
        camera_lock = 'Full body master wide shot, head to knees and floor completely visible with moderate headroom above head, stable eye-level tripod camera, camera never tilts down, strictly no partial close-up, graceful model proportions'
        orientation_lock = 'Charming graceful kneeling floor pose on knees, hand gracefully touching hair, natural anatomical alignment'
    elif is_rear_pose:
        camera_lock = CAMERA_LOCK_MODERATE
        orientation_lock = 'Consistent 3/4 rear body orientation, back of outfit strictly facing camera, head gracefully turned looking back over shoulder with natural anatomical neck alignment, strictly NO front chest on back'
    elif is_indoor:
        camera_lock = CAMERA_LOCK_INDOOR
        orientation_lock = 'Consistent natural frontal body orientation, upright posture, natural anatomical head-torso alignment'
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
    
    # Try dynamic vision analysis if image_url is available and no manual user_desc
    vision_data = None
    if not user_desc and image_url:
        print("  [Step 1 AI Vision] Analyzing reference image features via Agnes Vision LLM...")
        vision_data = vision_describe_character(image_url)

    if user_desc:
        subject_layer = user_desc
        body_guard = 'Exact same setting and 100% consistent character face, body proportions, figure silhouette, and bust-waist-hip curve strictly faithful to the reference image, natural graceful posture, identical clothing including identical garment length and hemline position, accessories, and shoes across all frames'
        parts = [camera_lock, FACE_LOCK, KINEMATIC_SAFETY, orientation_lock, subject_layer, body_guard]
    elif vision_data:
        face_desc = vision_data.get('face', '').strip()
        body_desc = vision_data.get('body_type', '').strip()
        outfit_desc = vision_data.get('outfit', '').strip()
        scene_desc = vision_data.get('scene', '').strip()

        face_layer = f"100% consistent character face with sharp detailed facial features, crystal clear skin texture: {face_desc}" if face_desc else FACE_LOCK
        subject_layer = f"A gorgeous East Asian woman strictly faithful to reference appearance, {body_desc}" if body_desc else 'A gorgeous East Asian woman strictly faithful to reference character identity and figure'
        outfit_layer = f"wearing exact same clothing strictly faithful to reference: {outfit_desc}. Identical garment dimensions and hemline position across all frames" if outfit_desc else 'wearing exact same clothing strictly faithful to reference image including identical garment length and hemline'
        scene_layer = f"Consistent background setting: {scene_desc}" if scene_desc else 'Exact same scene background and lighting faithful to the reference image'
        body_guard = '100% consistent character face, body proportions, figure silhouette, and bust-waist-hip curve strictly faithful to the reference image, natural graceful posture, identical clothing across all frames'
        parts = [camera_lock, face_layer, KINEMATIC_SAFETY, orientation_lock, subject_layer, outfit_layer, scene_layer, body_guard]
    else:
        subject_layer = 'A gorgeous East Asian woman strictly faithful to the character facial appearance and identity in the reference image'
        outfit_layer = ('wearing the exact same clothing strictly faithful to the reference image including '
                       'identical garment length, identical skirt or dress hemline position, identical sleeve length, '
                       'identical neckline shape. CRITICAL: if the reference image shows a short skirt ending '
                       'above the knees at mid-thigh level, the generated video must show the same short skirt '
                       'ending above the knees at mid-thigh level. If the reference shows a long skirt, keep it long. '
                       'Never elongate, shorten, or modify any garment dimensions from the reference. '
                       'Identical shoes and accessories across all frames')
        scene_layer = 'Exact same scene background, setting, and consistent lighting faithful to the reference image'
        body_guard = '100% consistent character face, body proportions, figure silhouette, and bust-waist-hip curve strictly faithful to the reference image, natural graceful posture, identical clothing including identical garment length and hemline position across all frames'
        parts = [camera_lock, FACE_LOCK, KINEMATIC_SAFETY, orientation_lock, subject_layer, outfit_layer, scene_layer, body_guard]
        
    prompt_lock = '. '.join([p.strip() for p in parts if p.strip()]) + '.'
    prompt_lock = re.sub(r'\.+', '.', prompt_lock).strip()
    return {
        'style': selected_style,
        'camera_lock': camera_lock,
        'subject_layer': subject_layer,
        'is_caucasian': is_caucasian,
        'is_indoor': is_indoor,
        'is_rear_pose': is_rear_pose,
        'is_kneeling_pose': is_kneeling_pose,
        'vision_data': vision_data,
        'full_prompt_lock': prompt_lock
    }

if __name__ == '__main__':
    import sys
    test_img = sys.argv[1] if len(sys.argv) > 1 else 'test.png'
    meta = analyze_character_and_scene(test_img, style_hint='street')
    print(meta['full_prompt_lock'])
