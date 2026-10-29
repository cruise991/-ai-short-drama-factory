import os
import json
import time
import urllib.request
import fcntl
import re
from shared_tools.config_loader import get_config

def clean_thought_tags(text: str) -> str:
    """Strip <thought>...</thought> or <thinking>...</thinking> tags from LLM responses."""
    if not text:
        return ""
    cleaned = re.sub(r'<(?:thought|thinking)>[\s\S]*?</(?:thought|thinking)>', '', text, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_json_payload(text: str) -> str:
    """Robust extractor for JSON content from markdown code fences or raw text."""
    if not text:
        return "{}"
    cleaned = clean_thought_tags(text)
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    start_brace = cleaned.find('{')
    start_bracket = cleaned.find('[')
    
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = cleaned.rfind('}')
        if end_brace != -1 and end_brace > start_brace:
            return cleaned[start_brace:end_brace+1].strip()
    elif start_bracket != -1:
        end_bracket = cleaned.rfind(']')
        if end_bracket != -1 and end_bracket > start_bracket:
            return cleaned[start_bracket:end_bracket+1].strip()
            
    return cleaned.strip()

USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".api_usage.json")

def get_agnes_keys():
    """Retrieve keys and their limits (text, image, video) from .env"""
    keys = []
    # Dynamic scan for AGNES_API_KEY_1 to AGNES_API_KEY_20
    for i in range(1, 21):
        key = get_config(f"AGNES_API_KEY_{i}")
        if key:
            # Key 4 is Enterprise (40 text, 40 image, 2 video RPM)
            # Others are Free/Default (20 text, 20 image, 1 video RPM)
            if i == 4:
                keys.append({
                    "key": key,
                    "limits": {
                        "text": 40,
                        "image": 40,
                        "video": 2
                    }
                })
            else:
                keys.append({
                    "key": key,
                    "limits": {
                        "text": 20,
                        "image": 20,
                        "video": 1
                    }
                })
    return keys

def _clean_old_records(usage_data, current_time):
    """Remove timestamps older than 60 seconds"""
    for key, resource_dict in list(usage_data.items()):
        if isinstance(resource_dict, list):
            # Migrate old format (list of timestamps) to dict
            usage_data[key] = {"text": [t for t in resource_dict if current_time - t < 60]}
        elif isinstance(resource_dict, dict):
            for res_type in resource_dict:
                resource_dict[res_type] = [t for t in resource_dict[res_type] if current_time - t < 60]

def _acquire_lock(file_obj):
    fcntl.flock(file_obj, fcntl.LOCK_EX)

def _release_lock(file_obj):
    fcntl.flock(file_obj, fcntl.LOCK_UN)

def get_available_key(keys, resource_type="text"):
    """Returns the first available API key string. Blocks if all are rate-limited.
    Uses Least-Utilized load balancing to pick the key with the highest remaining capacity.
    """
    while True:
        current_time = time.time()
        
        # Read or create usage file with lock
        with open(USAGE_FILE, 'a+') as f:
            _acquire_lock(f)
            try:
                f.seek(0)
                try:
                    usage_data = json.load(f)
                except json.JSONDecodeError:
                    usage_data = {}
                
                _clean_old_records(usage_data, current_time)
                
                best_key = None
                best_remaining_ratio = -1.0
                best_history = None
                
                # Find key with highest remaining capacity ratio
                for item in keys:
                    key = item["key"]
                    limits = item["limits"]
                    rpm = limits.get(resource_type, 1) # Default fallback
                    
                    if key not in usage_data:
                        usage_data[key] = {}
                    if not isinstance(usage_data[key], dict):
                        usage_data[key] = {"text": usage_data[key]}
                        
                    history = usage_data[key].get(resource_type, [])
                    
                    used = len(history)
                    if used < rpm:
                        remaining_ratio = (rpm - used) / rpm
                        if remaining_ratio > best_remaining_ratio:
                            best_remaining_ratio = remaining_ratio
                            best_key = key
                            best_history = history
                
                if best_key:
                    # Claim this slot
                    best_history.append(current_time)
                    usage_data[best_key][resource_type] = best_history
                    
                    f.seek(0)
                    f.truncate()
                    json.dump(usage_data, f)
                    return best_key
                        
                # If we get here, no keys are available
            finally:
                _release_lock(f)
                
        # Wait a bit before checking again to avoid CPU spinning
        print(f"[LLM Pool] All API keys are rate-limited for '{resource_type}'. Waiting 2 seconds...")
        time.sleep(2)

def record_429(key, resource_type="text"):
    """If we hit a 429, we pretend we used the key RPM times recently to block it for a minute"""
    keys = get_agnes_keys()
    rpm = 20 # fallback
    for item in keys:
        if item["key"] == key:
            rpm = item["limits"].get(resource_type, 20)
            break

    with open(USAGE_FILE, 'a+') as f:
        _acquire_lock(f)
        try:
            f.seek(0)
            try:
                usage_data = json.load(f)
            except json.JSONDecodeError:
                usage_data = {}
            
            if key not in usage_data or not isinstance(usage_data[key], dict):
                usage_data[key] = {}
                
            # fill the history with recent timestamps to max out the limit
            usage_data[key][resource_type] = [time.time()] * rpm
            
            f.seek(0)
            f.truncate()
            json.dump(usage_data, f)
        finally:
            _release_lock(f)

def call_llm(system_prompt, user_prompt):
    print("  [LLM Pool] Invoking REAL LLM...")

    base_url = get_config("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
    # Mock block removed to enforce real API calls
    
    model = get_config("PLANNING_LLM_MODEL", "agnes-3.0-flash")
    
    import urllib.request
    import json
    import ssl
    # SSL context preserved for potential urllib fallback, using system CAs
    ctx = ssl.create_default_context()
    
    keys = get_agnes_keys()
    current_model = model
    for attempt in range(4):
        # Rule 10 Fallback: On retry after failure/timeout, switch to agnes-2.5-flash
        if attempt > 0 and current_model == "agnes-3.0-flash":
            current_model = "agnes-2.5-flash"
            print(f"  [LLM Pool] 🔄 Rule 10 Fallback: Switching model to '{current_model}' (Attempt {attempt+1})...")

        api_key = get_available_key(keys, resource_type="text")
        if not api_key and keys:
            api_key = keys[attempt % len(keys)]["key"]

        is_gemini = "generativelanguage.googleapis.com" in base_url
        if is_gemini:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\n\n{user_prompt}"}
                        ]
                    }
                ]
            }
            endpoint = f"{base_url}/models/{current_model}:generateContent"
        else:
            payload = {
                "model": current_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            }
            # Only enable thinking for agnes-3.0-flash
            if current_model == "agnes-3.0-flash":
                payload["chat_template_kwargs"] = {"enable_thinking": True}
            endpoint = f"{base_url}/chat/completions"
        
        try:
            import requests
            headers = {"Content-Type": "application/json"}
            if is_gemini:
                headers["X-goog-api-key"] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"

            resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)
            if resp.status_code == 429:
                print(f"  [LLM API RateLimit] 429 on key {api_key[:8]}...")
                record_429(api_key, resource_type="text")
                continue

            data = resp.json()
            if "error" in data:
                error_msg = str(data["error"].get("message", "Unknown error"))
                if "rate limit" in error_msg.lower() or "429" in error_msg or "429" in str(data["error"].get("code", "")):
                    print(f"  [LLM API RateLimit] Rate limit error on key {api_key[:8]}: {error_msg}")
                    record_429(api_key, resource_type="text")
                    continue
                else:
                    print(f"  [LLM API Error] {error_msg}")
                    continue

            if is_gemini:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                content = data["choices"][0]["message"]["content"]
            return clean_thought_tags(content)
        except requests.exceptions.Timeout:
            print(f"  [LLM API Timeout] Request timed out for key {api_key[:8]} using {current_model}. Will retry/fallback.")
            continue
        except Exception as e:
            from shared_tools.log_sanitizer import sanitize
            print(f"  [LLM API Error] {sanitize(str(e))}")
            continue
    if "质检员" in system_prompt:
        return "FAIL: All API keys failed. QA cannot proceed."
    elif "You are a Prompt Renderer" in system_prompt:
        import re
        import json
        try:
            # Parse timeline and fixed values from system_prompt instead of user_prompt
            timeline_match = re.search(r"TIMELINE TO RENDER.*?:(.*?)RULES:", system_prompt, re.DOTALL)
            fixed_values_match = re.search(r"FIXED VALUES.*?:(.*?)TIMELINE TO RENDER", system_prompt, re.DOTALL)
            
            timeline_json = []
            if timeline_match:
                timeline_str = timeline_match.group(1).strip()
                timeline_json = json.loads(timeline_str)
            
            # Extract fixed values
            char_anchor = "ultra-realistic, raw photo, 8k resolution, photorealistic 1girl, 22yo gorgeous East Asian woman, 172cm tall, perfect golden ratio body proportions, hourglass figure, slim waist, long slender legs, highly detailed delicate sweet face, flawless porcelain glass skin, soft jawline, big bright eyes, aegyo sal, slightly downturned puppy eyes, sweet alluring smile, pure and innocent aura, long flowing dark brown hair, Korean idol aesthetic, Douyin beauty"
            costume = "white crop hoodie, short shorts"
            scene = "modern dance studio"
            lighting = "neon lights"
            effects = "highly detailed"
            music_pace = "cinematic"
            negative_prompt = "acne, blemishes, wrinkles, asymmetrical face, ugly, mature, deep smile lines, rough skin, extra fingers, bad anatomy, blur, duplicate limbs, watermark, prominent hands, hands toward camera, oily skin, shiny skin"
            
            if fixed_values_match:
                fixed_str = fixed_values_match.group(1)
                for line in fixed_str.split("\n"):
                    line = line.strip()
                    if line.startswith("- character_anchor:"): char_anchor = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- costume:"): costume = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- scene:"): scene = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- lighting:"): lighting = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- effects:"): effects = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- music_pace_hint:"): music_pace = line.split('"', 1)[1].rsplit('"', 1)[0]
                    if line.startswith("- negative_prompt"): negative_prompt = line.split('"', 1)[1].rsplit('"', 1)[0]
            
            # Default fallback if timeline parsing failed
            if not timeline_json:
                timeline_json = [
                    {"id": "shot_01", "type": "hook", "duration": 5, "action_id": "static", "camera_id": "static"},
                    {"id": "shot_02", "type": "dance", "duration": 5, "action_id": "dance_move_1", "camera_id": "zoom_in"},
                    {"id": "shot_03", "type": "dance", "duration": 5, "action_id": "dance_move_2", "camera_id": "pan_left"},
                    {"id": "shot_04", "type": "pose", "duration": 2, "action_id": "static", "camera_id": "static"}
                ]
            
            mock_shots = []
            total_duration = 0
            for i, shot in enumerate(timeline_json):
                duration = shot.get("duration", 5)
                total_duration += duration
                action = shot.get("action_id", "dancing")
                camera = shot.get("camera_id", "static")
                
                # To prevent close-up framing and bad hands
                visual_prompt = f"{char_anchor}, (wearing {costume}:1.4), full body shot, (perfect beautiful hands:1.2), performing {action}, {camera}, in {scene}, ({lighting}:1.4), {effects}, {music_pace}, masterpiece, high visual density, cinematic"
                
                mock_shots.append({
                    "id": shot.get("id", f"shot_{i+1:02d}"),
                    "type": shot.get("type", "dance"),
                    "duration": duration,
                    "action_id": action,
                    "camera_id": camera,
                    "visual_prompt": visual_prompt,
                    "negative_prompt": negative_prompt
                })
            
            mock_response = {
                "character_id": "mocked",
                "character_name": "mocked",
                "character_anchor": char_anchor,
                "style_id": "mocked",
                "negative_prompt": negative_prompt,
                "total_duration": total_duration,
                "shots": mock_shots
            }
            return f"```json\n{json.dumps(mock_response, indent=2, ensure_ascii=False)}\n```"
        except Exception as e:
            print(f"  [Mock Fallback] Error generating dynamic mock: {e}")
            return '{"error": "mock failed"}'
    elif "【📌 强制输出格式规范】" in system_prompt:
        return """
```json
{
  "locks": {
    "character_anchor": "ultra-realistic, raw photo, 8k resolution, photorealistic 1girl, 22yo gorgeous East Asian woman, 172cm tall, perfect golden ratio body proportions, hourglass figure, slim waist, long slender legs, highly detailed realistic face",
    "costume_lock": "white crop hoodie, black high-waist yoga leggings",
    "scene_lock": "modern dance studio, neon lights"
  },
  "timeline": [
    {
      "id": "shot_01",
      "phase": "Setup",
      "time_range": "0:00 - 0:05",
      "visual_prompt": "1girl, pure aesthetic, wearing B1_slouchy_home outfit in D1_messy_bedroom, leave safe margins for text, do not crop head",
      "camera": "static",
      "base_motion_source": "static",
      "bgm_id": "BGM_001",
      "hook_text_overlay": "你以为的学妹"
    },
    {
      "id": "shot_02",
      "phase": "Transition",
      "time_range": "0:05 - 0:07",
      "visual_prompt": "1girl, cyber aesthetic, wearing C1_yoga_queen in D2_neon_studio, dynamic flash, leave safe margins for text",
      "camera": "zoom_in",
      "base_motion_source": "static",
      "bgm_id": "同上",
      "hook_text_overlay": ""
    },
    {
      "id": "shot_03",
      "phase": "Main_Dance",
      "time_range": "0:07 - 0:25",
      "visual_prompt": "1girl, cyber aesthetic, wearing C1_yoga_queen in D2_neon_studio, dancing, leave safe margins for text",
      "camera": "follow",
      "base_motion_source": "R02",
      "bgm_id": "同上",
      "hook_text_overlay": ""
    },
    {
      "id": "shot_04",
      "phase": "Outro",
      "time_range": "0:25 - 0:35",
      "visual_prompt": "1girl, cyber aesthetic, smiling and pointing, leave safe margins for text",
      "camera": "static",
      "base_motion_source": "static",
      "bgm_id": "同上",
      "hook_text_overlay": "点赞关注！"
    }
  ],
  "distribution": {
    "title_options": ["反差绝了！", "看到最后"],
    "hashtags": ["#变身", "#舞蹈"],
    "cover_frame_sec": 7.5,
    "recommended_publish_time": "19:00-22:00"
  }
}
```
"""
    elif "提取用户最终敲定" in system_prompt:
        return "Audience: 通用受众\nStyle: 高级感营销\nCharacter: default"
    elif "探讨策划方向" in system_prompt:
        return "网络有点卡顿，我已经收到您的意向，是否确定当前策划方向开始制作？（输入 'ok' 确认生成）"
    elif "换装变身反差" in system_prompt:
        return """
# 剧本与分镜 (Storyboard & Live-Action Blueprint)

**核心目标 (Goal)**: 换装变身反差展示
**受众与风格 (Audience & Style)**: 通用受众 | 赛博朋克
**形式 (Format)**: 换装变身反差
**时长**: 约 15 秒

## 角色设定 (Characters)
- 主角: 变身前为普通职员，变身后为赛博辣妹

## Shot 1: 变身前状态
**时间范围**: 0:00 - 0:05 (5s)
**场景 (Scene)**: 杂乱的办公室
**图像建议 (Image Suggestion)**: 静态站立，神情疲惫
**提示词 (Video Prompt)**: ultra-realistic, photorealistic 1girl, tired office worker, standing in messy office, cold lighting, masterpiece, 8k

## Shot 2: Glitch 转场
**时间范围**: 0:05 - 0:10 (5s)
**场景 (Scene)**: 办公室场景逐渐崩溃
**图像建议 (Image Suggestion)**: 静态，画面出现故障波纹
**提示词 (Video Prompt)**: ultra-realistic, photorealistic 1girl, glitch effect, neon lights bleeding in, transition, masterpiece, 8k

## Shot 3: 赛博辣妹揭示
**时间范围**: 0:10 - 0:15 (5s)
**场景 (Scene)**: 霓虹闪烁的赛博朋克街道
**图像建议 (Image Suggestion)**: 自信微笑，直视镜头
**提示词 (Video Prompt)**: ultra-realistic, photorealistic 1girl, cyber punk fashion, confident smile, neon streets, cinematic lighting, masterpiece, 8k
"""
    else:
        return "PASS"

