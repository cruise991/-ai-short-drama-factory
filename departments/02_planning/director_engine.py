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
    """加载所有舞蹈资产，返回统一字典。"""
    assets = {
        "trends":       _load("trends.json"),
        "characters":   _load("characters.json"),
        "dance_moves":  _load("dance_moves.json"),
        "camera_moves": _load("camera_moves.json"),
        "shot_templates":  _load("shot_templates.json"),
        "rhythm_templates": _load("rhythm_templates.json"),
        "hooks":        _load("hooks.json"),
        "poses":        _load("poses.json"),
        "transition_graph": _load("transition_graph.json"),
        "prompt_template":  _load("prompt_template.json"),
        "negative_prompts": _load("negative_prompts.json"),
        "rules":        _load("rules.json"),
        "styles":       {},
    }
    # 加载所有风格包
    styles_dir = os.path.join(_DANCE_ASSETS_DIR, "styles")
    for fpath in glob.glob(os.path.join(styles_dir, "*.json")):
        style_id = os.path.splitext(os.path.basename(fpath))[0]
        with open(fpath, "r", encoding="utf-8") as f:
            assets["styles"][style_id] = json.load(f)
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
def select_style_pack(character_id: str, rules: dict, styles: dict,
                      trend_id: Optional[str] = None) -> tuple:
    """
    根据角色规则 + 热点趋势选择风格包。
    优先选与当前热点 preferred_style 对齐的风格包，并在该风格中加权。
    返回 (style_id, style_pack_dict)
    """
    char_rules = rules.get(character_id, {})
    preferred_styles = char_rules.get("preferred_styles", {})

    if not preferred_styles:
        # fallback: 随机从已有风格包中选
        style_id = random.choice(list(styles.keys()))
        return style_id, styles[style_id]

    style_id, _ = weighted_sample(preferred_styles)
    if style_id not in styles:
        style_id = list(styles.keys())[0]

    return style_id, styles[style_id]


# ─── 从风格包抽样单个属性 ──────────────────────────────────────────────────────
def _pick_from_style(style_pack: dict, attr: str) -> str:
    """从风格包的某个属性（scenes/lighting/costumes/等）加权抽样，返回 prompt 字符串。"""
    options = style_pack.get(attr, {})
    if not options:
        return ""
    key, val = weighted_sample(options)
    return val.get("prompt", val) if isinstance(val, dict) else str(val)


# ─── 节奏模板选择 ─────────────────────────────────────────────────────────────
def select_rhythm(character_id: str, rules: dict, rhythm_templates: dict,
                  total_duration: int) -> tuple:
    """选择最接近目标时长的节奏模板，优先从角色偏好中选。"""
    char_rules = rules.get(character_id, {})
    preferred = char_rules.get("preferred_rhythms", list(rhythm_templates.keys()))

    # 过滤出时长接近的模板
    candidates = {
        k: v for k, v in rhythm_templates.items()
        if k in preferred and abs(v["total_seconds"] - total_duration) <= 4
    }
    if not candidates:
        candidates = {k: rhythm_templates[k] for k in preferred if k in rhythm_templates}
    if not candidates:
        candidates = rhythm_templates

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
    hook_id = list_weighted_sample(char_rules.get("preferred_hooks", list(hooks.keys())))
    hook_data = hooks.get(hook_id, hooks[list(hooks.keys())[0]])

    # 选 pose
    pose_id = list_weighted_sample(char_rules.get("preferred_poses", list(poses.keys())))
    pose_data = poses.get(pose_id, poses[list(poses.keys())[0]])

    # 中间动作：从 dance_moves 中不重复地抽取
    middle_count = n - 2
    all_move_ids = [k for k in dance_moves.keys() if not k.startswith("_")]
    random.shuffle(all_move_ids)
    middle_moves = all_move_ids[:middle_count]

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
            move_id = middle_moves[idx - 1] if (idx - 1) < len(middle_moves) else all_move_ids[0]
            move_data = dance_moves.get(move_id, {})
            shot["type"] = "dance"
            shot["action_id"] = move_id
            shot["action_prompt"] = move_data.get("prompt", "")
            shot["camera_prompt"] = camera_moves.get(camera_sequence[idx], {}).get("prompt", "")

        timeline.append(shot)

    return timeline


# ─── 主入口 ───────────────────────────────────────────────────────────────────
def direct(character_id: str, total_duration: int,
           trend_id: Optional[str] = None) -> dict:
    """
    Layer 4 + 5 主入口。
    输入: 角色 ID + 视频总时长（秒）+ 可选热点 ID
    输出: 完整导演决策 dict（含 timeline 和帧间连续性标注）
    """
    assets = load_dance_assets()

    # 检查角色存在
    char_data = assets["characters"].get(character_id)
    if not char_data:
        raise ValueError(f"Character '{character_id}' not found in dance/characters.json")

    char_rules = assets["rules"].get(character_id, {})

    # Layer 1: 热点（可选，影响偏好权重）
    active_trend = None
    if trend_id and trend_id in assets["trends"]:
        active_trend = assets["trends"][trend_id]

    # Layer 2 → 3: 角色 → 风格包选择
    style_id, style_pack = select_style_pack(
        character_id, assets["rules"], assets["styles"], trend_id
    )

    # Layer 3: 从风格包加权抽样各属性
    scene_prompt    = _pick_from_style(style_pack, "scenes")
    lighting_prompt = _pick_from_style(style_pack, "lighting")
    costume_prompt  = _pick_from_style(style_pack, "costumes")
    hairstyle_prompt = _pick_from_style(style_pack, "hairstyles")
    expression_prompt = _pick_from_style(style_pack, "expressions")
    effects_prompt  = style_pack.get("effects", {}).get("prompt", "")
    style_negative  = style_pack.get("effects", {}).get("negative", "")
    music_pace_hint = style_pack.get("music_pace_hint", "")
    music_style     = style_pack.get("music_style", "")

    # Layer 4: 导演引擎 — 节奏 + 镜头序列选择
    rhythm_id, rhythm = select_rhythm(
        character_id, assets["rules"], assets["rhythm_templates"], total_duration
    )

    template_candidates = char_rules.get("preferred_shot_templates", list(assets["shot_templates"].keys()))
    template_id = list_weighted_sample([t for t in template_candidates if t in assets["shot_templates"]]
                                       or list(assets["shot_templates"].keys()))
    shot_template = assets["shot_templates"][template_id]

    # Layer 4: 组装原始 Timeline
    raw_timeline = build_timeline(
        character_id, assets["rules"], rhythm, shot_template,
        assets["hooks"], assets["dance_moves"], assets["camera_moves"],
        assets["poses"], char_rules
    )

    # Layer 5: Temporal Engine — 注入帧间连续性
    enriched_timeline = apply_temporal_continuity(raw_timeline, assets["transition_graph"])

    # 负面提示词
    neg = assets["negative_prompts"]
    negative_prompt = f"{neg.get('universal', '')}, {neg.get('dance_specific', '')}, {style_negative}"

    return {
        "character_id":    character_id,
        "character_name":  char_data.get("name", character_id),
        "anchor_prompt":   char_data.get("anchor_prompt", ""),
        "style_id":        style_id,
        "trend_id":        trend_id,
        "hairstyle_prompt":   hairstyle_prompt,
        "expression_prompt":  expression_prompt,
        "costume_prompt":     costume_prompt,
        "scene_prompt":       scene_prompt,
        "lighting_prompt":    lighting_prompt,
        "effects_prompt":     effects_prompt,
        "music_style":        music_style,
        "music_pace_hint":    music_pace_hint,
        "negative_prompt":    negative_prompt,
        "rhythm_id":          rhythm_id,
        "shot_template_id":   template_id,
        "total_duration":     rhythm.get("total_seconds", total_duration),
        "timeline":           enriched_timeline
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
