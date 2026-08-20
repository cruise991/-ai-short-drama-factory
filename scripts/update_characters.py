import json
import glob
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base_path = os.path.join(base_dir, "assets", "dance", "01_characters", "ips", "")
files = glob.glob(base_path + "*.json")

aesthetic_prefix = "ultra-realistic, 8k resolution, raw photo, DSLR, shot on 85mm f/1.8. "
aesthetic_suffix = "bright modern luxury interior background, daylight coming from large windows, soft cinematic lighting, bright and airy color grading, high-key, shallow depth of field, bokeh, masterpiece, best quality."

# Standard skin and face updates
SKIN = "glass glowing skin, ultra-detailed skin texture, realistic pores, fair skin with slight natural blush"

for f in files:
    if "Yumi" in f: continue
    
    with open(f, 'r') as file:
        data = json.load(file)
        
    # Inject skin
    data['skin'] = SKIN
    
    # Inject face enhancement
    if "highly detailed realistic face" not in data['face']:
        data['face'] = "gorgeous delicate face, highly detailed realistic face, " + data['face']
    
    # Update anchor_prompt
    # Extract the core character description from the old prompt
    old_prompt = data.get('anchor_prompt', '')
    
    # Let's just rebuild the anchor prompt using the attributes to ensure consistency
    parts = [
        aesthetic_prefix,
        f"1girl, {data.get('age', 20)}yo gorgeous fashion model, ",
        f"{data.get('face')}, ",
        f"{data.get('skin')}, ",
        f"{data.get('hair_color')} {data.get('default_hairstyle').replace('_', ' ')} hair, ",
        f"{data.get('height')}, {data.get('build')}, ",
        f"vibe: {data.get('vibe')}. ",
        aesthetic_suffix
    ]
    
    data['anchor_prompt'] = "".join(parts)
    
    with open(f, 'w') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        
print("Updated all characters successfully.")
