"""
director_engine.py — Layer 4 + Layer 5 (Director Engine + Temporal Engine)
Branch 3 舞蹈流专属。不被 Branch 1/2 调用。

主入口: direct(character_id, total_duration, trend_id=None)
输出: 完整的导演决策 dict，包含 timeline + 帧间连续性标注
"""

import json
import os
import random
import glob
from typing import Optional

# ─── 路径配置 ────────────────────────────────────────────────────────────────
_DANCE_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "../../assets/dance")


# ─── 资产加载 ────────────────────────────────────────────────────────────────
_CACHE: dict = {}

def _load(filename: str) -> dict:
    """加载单个 JSON 文件，带缓存。"""
    path = os.path.join(_DANCE_ASSETS_DIR, filename)
    if path not in _CACHE:
        with open(path, "r", encoding="utf-8") as f:
            _CACHE[path] = json.load(f)
    return _CACHE[path]


def load_dance_assets() -> dict:
    """加载所有舞蹈资产，返回统一字典。支持模块化新目录结构。"""
    assets = {
        "trends":           _load("_core/trends.json"),
        "rules":            _load("_core/rules.json"),
        "prompt_template":  _load("_core/prompt_template.json"),
        "negative_prompts": _load("_core/negative_prompts.json"),
        "quality_weights":  _load("_core/quality_weights.json"),

        "dance_moves":      _load("04_actions/basic_moves.json"),
        "hooks":            _load("04_actions/hooks.json"),
        "poses":            _load("04_actions/poses.json"),
        "choreography":     _load("04_actions/choreography.json"),

        "camera_moves":     _load("06_camera_and_edit/camera_moves.json"),
        "shot_templates":   _load("06_camera_and_edit/shot_templates.json"),
        "transition_graph": _load("06_camera_and_edit/transition_graph.json"),
        "edit_effects":     _load("06_camera_and_edit/edit_effects.json"),

        "rhythm_templates": _load("05_music/rhythm_templates.json"),
        "music_genres":     _load("05_music/genres.json"),

        "hairstyles":       _load("01_characters/hairstyles.json"),
        "makeup":           _load("01_characters/makeup.json"),
        "expressions":      _load("01_characters/expressions.json"),

        "characters":       {},
        "outfits":          {},
        "scenes":           {}
    }

    def _load_dir(dir_name):
        d = {}
        dir_path = os.path.join(_DANCE_ASSETS_DIR, dir_name)
        if os.path.exists(dir_path):
            import glob
            for fpath in glob.glob(os.path.join(dir_path, "*.json")):
                sub_id = os.path.splitext(os.path.basename(fpath))[0]
                with open(fpath, "r", encoding="utf-8") as f:
                    d[sub_id] = json.load(f)
        return d

    assets["outfits"] = _load_dir("02_outfits")
    assets["scenes"] = _load_dir("03_scenes")

    # 加载所有角色 IP
    chars_dir = os.path.join(_DANCE_ASSETS_DIR, "01_characters/ips")
    if os.path.exists(chars_dir):
        import glob
        for fpath in glob.glob(os.path.join(chars_dir, "*.json")):
            char_id = os.path.splitext(os.path.basename(fpath))[0]
            with open(fpath, "r", encoding="utf-8") as f:
                assets["characters"][char_id] = json.load(f)

    return assets


# ─── 加权抽样 ────────────────────────────────────────────────────────────────
def weighted_sample(options: dict, exclude_keys: list = None) -> tuple:
    """
    从带权重的 dict 中按概率抽样。
    options: {key: {weight: float, ...}, ...} 或 {key: float, ...}
    返回 (key, value_or_weight)
    """
    exclude_keys = exclude_keys or []
    keys, weights = [], []
    for k, v in options.items():
        if k.startswith("_") or k in exclude_keys:
            continue
        w = v.get("weight", v) if isinstance(v, dict) else v
        keys.append(k)
        weights.append(float(w))

    if not keys:
        raise ValueError(f"weighted_sample: no valid options in {list(options.keys())}")

    total = sum(weights)
    probs = [w / total for w in weights]
    chosen = random.choices(keys, weights=probs, k=1)[0]
    return chosen, options[chosen]


def list_weighted_sample(options: list) -> str:
    """从列表中随机选一项（等权重）。"""
    return random.choice(options)


# ─── 风格包选择 ───────────────────────────────────────────────────────────────
# ─── 节奏模板选择 ─────────────────────────────────────────────────────────────
def select_rhythm(character_id: str, rules: dict, rhythm_templates: dict,
                  total_duration: int) -> tuple:
    """选择最接近目标时长的节奏模板，优先从角色偏好中选。"""
    char_rules = rules.get(character_id, {})
    preferred = char_rules.get("preferred_rhythms", list(rhythm_templates.keys()))

    # 过滤出时长接近的模板
    candidates = {
        k: v for k, v in rhythm_templates.items()
        if not k.startswith("_") and k in preferred and abs(v["total_seconds"] - total_duration) <= 6
    }
    if not candidates:
        candidates = {k: rhythm_templates[k] for k in preferred if k in rhythm_templates and not k.startswith("_")}
    if not candidates:
        candidates = {k: v for k, v in rhythm_templates.items() if not k.startswith("_")}

    rhythm_id = list_weighted_sample(list(candidates.keys()))
    return rhythm_id, rhythm_templates[rhythm_id]


# ─── Temporal Engine: 推断朝向 ───────────────────────────────────────────────
def infer_facing(action_id: str, facing_infer: dict) -> str:
    """根据动作 ID 推断身体朝向。"""
    return facing_infer.get(action_id, "front")


def _legal_facing(current: str, body_facing_graph: dict) -> list:
    return body_facing_graph.get(current, ["front"])


# ─── Temporal Engine: 主函数 ──────────────────────────────────────────────────
def apply_temporal_continuity(timeline: list, graph: dict) -> list:
    """
    Layer 5: 时间连续性引擎。
    校验并修正相邻 shot 间的动作/运镜/朝向合法性。
    为每个 shot 注入 continuity_prefix 和 exit_state。
    """
    dance_graph  = graph.get("dance_transitions", {})
    camera_graph = graph.get("camera_transitions", {})
    body_facing  = graph.get("body_facing", {})
    facing_infer = graph.get("facing_infer", {})

    for i, shot in enumerate(timeline):
        action_id = shot.get("action_id", "body_wave")
        camera_id = shot.get("camera_id", "static_wide")

        if i == 0:
            # 第一帧无约束
            shot["continuity_prefix"] = ""
        else:
            prev = timeline[i - 1]
            prev_exit = prev.get("exit_state", {})
            prev_action = prev_exit.get("action", "body_wave")
            prev_camera = prev_exit.get("camera", "static_wide")
            prev_facing = prev_exit.get("facing", "front")

            # 1. 检查并修正动作合法性
            legal_actions = dance_graph.get(prev_action, [])
            if legal_actions and action_id not in legal_actions:
                action_id = legal_actions[0]
                shot["action_id"] = action_id

            # 2. 检查并修正运镜合法性
            legal_cameras = camera_graph.get(prev_camera, [])
            if legal_cameras and camera_id not in legal_cameras:
                camera_id = legal_cameras[0]
                shot["camera_id"] = camera_id

            # 3. 推断当前朝向并生成连续性前缀
            current_facing = infer_facing(action_id, facing_infer)
            legal_facings = _legal_facing(prev_facing, body_facing)

            if current_facing not in legal_facings:
                # 朝向非法：描述平滑过渡
                shot["continuity_prefix"] = (
                    f"smoothly transitioning from {prev_action} with body turning "
                    f"from {prev_facing} to {current_facing}"
                )
            else:
                shot["continuity_prefix"] = (
                    f"continuing from {prev_action}, body facing {prev_facing}"
                )

        # 4. 记录本帧结束状态
        final_action_id = shot.get("action_id", action_id)
        final_camera_id = shot.get("camera_id", camera_id)
        shot["exit_state"] = {
            "action":  final_action_id.split("+")[-1].strip(),
            "camera":  final_camera_id,
            "facing":  infer_facing(final_action_id.split("+")[-1].strip(), facing_infer)
        }

    return timeline


# ─── Timeline 组装 ────────────────────────────────────────────────────────────
def build_timeline(character_id: str, rules: dict, rhythm: dict, shot_template: dict,
                   hooks: dict, dance_moves: dict, camera_moves: dict, poses: dict,
                   char_rules: dict) -> list:
    """
    按节奏模板和镜头序列模板组装原始 timeline。
    Hook 强制在第一个 shot，Pose 强制在最后一个 shot。
    """
    beats = rhythm.get("beats", [2, 3, 3, 2, 2])
    camera_sequence = shot_template.get("sequence", ["static_wide"] * len(beats))

    # 确保序列长度匹配
    n = len(beats)
    while len(camera_sequence) < n:
        camera_sequence.append(camera_sequence[-1])
    camera_sequence = camera_sequence[:n]

    # 选 hook
    hook_keys = [k for k in hooks.keys() if not k.startswith("_")]
    hook_id = list_weighted_sample(char_rules.get("preferred_hooks", hook_keys))
    hook_data = hooks.get(hook_id, hooks[hook_keys[0]])

    # 选 pose
    pose_keys = [k for k in poses.keys() if not k.startswith("_")]
    pose_id = list_weighted_sample(char_rules.get("preferred_poses", pose_keys))
    pose_data = poses.get(pose_id, poses[pose_keys[0]])

    # 中间动作：提升 Hooks 和 Wave 动作的权重
    middle_count = n - 2
    middle_moves_pool = []
    
    # 注入高级 Hook 动作，权重 x3
    for h_id in hooks:
        if not h_id.startswith("_"):
            middle_moves_pool.extend([f"HOOK:{h_id}"] * 3)
            
    for k, v in dance_moves.items():
        if k.startswith("_"): continue
        if "prompt" in v: # flat
            if "wave" in k or "hip" in k:
                middle_moves_pool.extend([f"MOVE:{k}"] * 2)
            else:
                middle_moves_pool.append(f"MOVE:{k}")
        else: # nested
            for sub_k, sub_v in v.items():
                if "wave" in sub_k or "hip" in sub_k:
                    middle_moves_pool.extend([f"MOVE:{k}/{sub_k}"] * 2)
                else:
                    middle_moves_pool.append(f"MOVE:{k}/{sub_k}")
                
    if not middle_moves_pool:
        middle_moves_pool = ["MOVE:hand_movements/flower_basic"]
        
    random.shuffle(middle_moves_pool)
    middle_moves = []
    for m in middle_moves_pool:
        if m not in middle_moves:
            middle_moves.append(m)
            if len(middle_moves) >= middle_count:
                break

    timeline = []
    for idx in range(n):
        shot = {
            "shot": idx + 1,
            "duration": beats[idx],
            "camera_id": camera_sequence[idx],
            "continuity_prefix": None,
            "exit_state": {}
        }

        if idx == 0:
            # Hook
            shot["type"] = "hook"
            shot["action_id"] = hook_id
            shot["action_prompt"] = hook_data.get("prompt", "")
            # Hook 有自己专属的运镜，覆盖 shot_template 的运镜
            shot["camera_id"] = hook_data.get("camera_key", camera_sequence[0])
            shot["camera_prompt"] = hook_data.get("camera_prompt", "")
        elif idx == n - 1:
            # Pose
            shot["type"] = "pose"
            shot["action_id"] = pose_id
            shot["action_prompt"] = pose_data.get("prompt", "")
            shot["camera_prompt"] = camera_moves.get(camera_sequence[idx], {}).get("prompt", "")
        else:
            # 中间舞蹈动作
            move_id_raw = middle_moves[idx - 1] if (idx - 1) < len(middle_moves) else middle_moves[0]
            
            if move_id_raw.startswith("HOOK:"):
                move_id = move_id_raw[5:]
                move_data = hooks.get(move_id, {})
            else:
                move_id = move_id_raw[5:]
                if "/" in move_id:
                    cat, sub = move_id.split("/")
                    move_data = dance_moves.get(cat, {}).get(sub, {})
                else:
                    move_data = dance_moves.get(move_id, {})
                
            shot["type"] = "dance"
            shot["action_id"] = move_id
            shot["action_prompt"] = move_data.get("prompt", "")
            shot["camera_prompt"] = camera_moves.get(camera_sequence[idx], {}).get("prompt", "")

        timeline.append(shot)

    return timeline


# ─── 主入口 ───────────────────────────────────────────────────────────────────
def direct(character_id: str, total_duration: int,
           trend_id: Optional[str] = None, module_params: Optional[dict] = None,
           custom_beats: Optional[list] = None) -> dict:
    """
    Layer 4 + 5 主入口。
    输入: 角色 ID + 视频总时长（秒）+ 可选热点 ID
    输出: 完整导演决策 dict（含 timeline 和帧间连续性标注）
    """
    assets = load_dance_assets()

    # 检查角色存在
    char_data = assets["characters"].get(character_id)
    if not char_data:
        # Fallback 到第一个角色
        if assets["characters"]:
            character_id = list(assets["characters"].keys())[0]
            char_data = assets["characters"][character_id]
        else:
            raise ValueError(f"Character '{character_id}' not found and no characters available in dance/characters/")

    char_rules = assets["rules"].get(character_id, {})

    # Layer 1: 热点（可选，影响偏好权重）
    active_trend = None
    if trend_id and trend_id in assets["trends"]:
        active_trend = assets["trends"][trend_id]

    # ─── 新增模块化抽样 ───
    def _sample_modular(category_dict, target_style=None):
        if not category_dict: return ""
        keys = list(category_dict.keys())
        if not keys: return ""
        
        if target_style:
            filtered_keys = [k for k in keys if category_dict[k].get("style") == target_style]
            if filtered_keys:
                chosen = random.choice(filtered_keys)
                return category_dict[chosen].get("prompt", "")
                
        chosen = random.choice(keys)
        item = category_dict[chosen]
        return item.get("prompt", "")

    preferred_style = active_trend.get("preferred_style") if active_trend else None

    hairstyle_prompt = _sample_modular(assets["hairstyles"], target_style=preferred_style)
    makeup_style = _sample_modular(assets["makeup"], target_style=preferred_style)
    
    # 智能场景匹配：优先从所有场景（indoor/outdoor）中匹配目标风格
    matched_scenes = []
    if preferred_style:
        for cat in ["indoor", "outdoor"]:
            cat_scenes = assets["scenes"].get(cat, {})
            for k, v in cat_scenes.items():
                if v.get("style") == preferred_style:
                    matched_scenes.append(v)
    if matched_scenes:
        scene_location = random.choice(matched_scenes).get("prompt", "")
    else:
        scene_cat = random.choice(["indoor", "outdoor"])
        scene_location = _sample_modular(assets["scenes"].get(scene_cat, {}))

    # 灯光环境暂使用硬编码，未来可进一步拆分为独立的 lighting.json
    lighting_prompt = "lower overall exposure, avoid softbox overexposure, use soft diffused light, retain skin and clothing texture details. Main light: soft frontal diffused light simulating window natural light. Fill light: low intensity side light to supplement shadow details. Rim light: weak back-side light outlining hair and body edges. Avoid: direct harsh spotlights, overexposed highlights, glaring reflections"
    
    # 表情和剪辑特效现在也走模块化
    expression_prompt = _sample_modular(assets["expressions"]) or "confident smile"
    effects_prompt  = _sample_modular(assets["edit_effects"])
    style_negative  = "" # 废弃风格包特有负面词
    
    # 音乐流派模块化
    music_genre_data = {}
    music_genres = assets["music_genres"].get("genres", {})
    if music_genres:
        genre_id = random.choice(list(music_genres.keys()))
        music_genre_data = music_genres[genre_id]
        
    music_pace_hint = music_genre_data.get("style", "")
    music_style     = genre_id if music_genres else ""

    # Layer 4: 导演引擎 — 节奏 + 镜头序列选择
    if custom_beats:
        rhythm = {"total_seconds": sum(custom_beats), "beats": custom_beats, "desc": "Custom LLM Beats"}
        rhythm_id = "custom_llm_beats"
    else:
        rhythm_id, rhythm = select_rhythm(
            character_id, assets["rules"], assets["rhythm_templates"], total_duration
        )

    template_candidates = char_rules.get("preferred_shot_templates", [k for k in assets["shot_templates"].keys() if not k.startswith("_")])
    template_id = list_weighted_sample([t for t in template_candidates if t in assets["shot_templates"] and not t.startswith("_")]
                                       or [k for k in assets["shot_templates"].keys() if not k.startswith("_")])
    shot_template = assets["shot_templates"][template_id]

    # Layer 4: 组装原始 Timeline
    raw_timeline = build_timeline(
        character_id, assets["rules"], rhythm, shot_template,
        assets["hooks"], assets["dance_moves"], assets["camera_moves"],
        assets["poses"], char_rules
    )

    # Layer 5: Temporal Engine — 注入帧间连续性
    enriched_timeline = apply_temporal_continuity(raw_timeline, assets["transition_graph"])

    # 负面提示词 (Stage 1) - 强力防模糊 + 防扭曲防暴露 + 防暗调 + 强化解剖学防变异 + 防背包配饰 + 审美红线
    stage_1_negative = "nsfw, nude, cleavage exposure, explicit, deformed, unnatural proportions, bad anatomy, broken limbs, motion blur, dancing, running, floating hair, dynamic pose, mid-air, depth of field blur, action lines, flying clothes, blur, watermark, changing clothes, ugly, poor quality, heavy makeup, strong lip gloss, water drops on lips, strong light, high contrast, smooth plastic skin, unnatural lighting, dark lighting, poorly drawn face, face morphing, dirty background, extra arms, three arms, extra hands, extra legs, three legs, mutated legs, deformed legs, missing limbs, mutated hands, multiple people, cloned body, blush, red cheeks, excessive blush, unnatural red cheeks, plastic skin, oily face, shiny skin, asymmetrical eyes, handbag, bag, backpack, purse, holding bag, holding accessories, messy lighting equipment, messy background"

    # 从热点中解析 BGM 偏好，否则默认 BGM_001
    bgm_id = "BGM_001"
    if active_trend and active_trend.get("preferred_bgm"):
        bgm_id = active_trend["preferred_bgm"]

    # --- Dual-Stage Loop Pattern Router ---
    vibe = module_params.get("vibe", "pure") if module_params else "pure"
    loop_router = {
        "psychedelic": {
            "loop_pattern": "Hand Lock",
            "anchor_prompt": "hands on cheeks forming a heart or resting on cheeks, with a wink, hands will bounce back to cheeks at the end"
        },
        "sad": {
            "loop_pattern": "Mirror Symmetry",
            "anchor_prompt": "one hand gently playing with high ponytail, looking directly at the camera, slightly biting lip, hand naturally returns to hair at the end"
        },
        "pure": {
            "loop_pattern": "Circle Flow",
            "anchor_prompt": "one hand playing with hair, slightly raising chin"
        },
        "energy": {
            "loop_pattern": "Beat Drop",
            "anchor_prompt": "hands in pockets or one hand pulling jacket edge, contemptuous look, hands return to pockets at the end"
        }
    }
    
    router_info = loop_router.get(vibe, loop_router["pure"])
    golden_anchor = router_info["anchor_prompt"]
    loop_pattern = router_info["loop_pattern"]

    # 动态注入安全词、细分身材和强质感服装
    safety_words = "sfw, elegant, high fashion, aesthetic, monetizable"
    
    if vibe in ["energy", "psychedelic"]:
        costume_modifiers = "stylish athletic wear"
    else:
        costume_modifiers = "casual cute fashion"

    aesthetic_prompt = "hyper-realistic skin texture, clearly visible pores, perfectly even skin tone without blush, raw natural bare face makeup look, soft matte natural lip color without gloss or water drops, no heavy makeup, not painted feeling, no smooth plastic look, shallow depth of field blur for background"
    stage_1_image_prompt = f"{safety_words}. {char_data.get('anchor_prompt', '')}, {golden_anchor}. {aesthetic_prompt}. {costume_modifiers}. {scene_location}. {lighting_prompt}. perfect human anatomy, exactly two arms and two legs."

    return {
        "character_id":    character_id,
        "character_name":  char_data.get("name", character_id),
        "trend_id":        trend_id,
        
        "stage_1_image": {
            "prompt": stage_1_image_prompt,
            "negative_prompt": stage_1_negative,
            "golden_anchor": golden_anchor
        },
        
        "stage_2_video": {
            "loop_pattern": loop_pattern,
            "timeline": enriched_timeline,
            "camera_control": "Locked camera, no transitions"
        },
        
        "metadata": {
            "vibe": vibe,
            "outfit_contrast": module_params.get("outfit_contrast", "") if module_params else ""
        }
    }


# ─── CLI 测试入口 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json as _json

    char = sys.argv[1] if len(sys.argv) > 1 else "C001_Luna"
    dur  = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    trend = sys.argv[3] if len(sys.argv) > 3 else None

    result = direct(char, dur, trend)
    print(_json.dumps(result, indent=2, ensure_ascii=False))
