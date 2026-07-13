"""
quality_evaluator.py — Layer 8 (Quality Evaluator)
Branch 3 舞蹈流专属。在 LLM 渲染 Prompt 后、写入 storyboard 前自动调用。
不达标自动触发重试（最多 max_retries 次）。
"""

import json
import os
from typing import Union

# ─── 权重配置路径 ──────────────────────────────────────────────────────────────
_QUALITY_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__), "../../assets/dance/quality_weights.json"
)

def _load_quality_weights() -> dict:
    with open(_QUALITY_WEIGHTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── 各维度检查函数 ────────────────────────────────────────────────────────────
def _check_character_consistency(storyboard: dict, weight: float) -> float:
    """
    25分：所有 shot 的 visual_prompt 是否保留了 anchor_prompt 关键词。
    策略：检查 anchor_prompt 的前10个词是否出现在每个 shot 的 visual_prompt 中。
    """
    anchor = storyboard.get("anchor_prompt", "")
    if not anchor:
        return weight * 0.5  # 没有 anchor 扣半分

    # 提取 anchor 的关键词（前15个词，过滤短词）
    anchor_keywords = [w.lower().strip(",.") for w in anchor.split()
                       if len(w) > 4][:15]

    shots = storyboard.get("shots", [])
    if not shots:
        return 0.0

    scores = []
    for shot in shots:
        vp = shot.get("visual_prompt", "").lower()
        hits = sum(1 for kw in anchor_keywords if kw in vp)
        scores.append(hits / max(len(anchor_keywords), 1))

    avg_score = sum(scores) / len(scores)
    return weight * avg_score


def _check_temporal_continuity(storyboard: dict, weight: float) -> float:
    """
    20分：相邻 shot 的动作/运镜是否在合法过渡路径上。
    检查 storyboard 中 timeline 的 exit_state 链。
    """
    shots = storyboard.get("shots", [])
    if len(shots) < 2:
        return weight  # 不足2个shot无法判断，给满分

    valid_transitions = 0
    total_transitions = len(shots) - 1

    # 尝试加载 transition_graph
    try:
        graph_path = os.path.join(os.path.dirname(__file__),
                                  "../../assets/dance/transition_graph.json")
        with open(graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)
        dance_graph  = graph.get("dance_transitions", {})
        camera_graph = graph.get("camera_transitions", {})
    except Exception:
        return weight * 0.7  # 加载失败，保守给70%

    for i in range(1, len(shots)):
        prev_exit = shots[i-1].get("exit_state", {})
        curr_action = shots[i].get("action_id", "")
        curr_camera = shots[i].get("camera_id", "")
        prev_action = prev_exit.get("action", "")
        prev_camera = prev_exit.get("camera", "")

        action_ok = (prev_action not in dance_graph or
                     curr_action in dance_graph.get(prev_action, []))
        camera_ok = (prev_camera not in camera_graph or
                     curr_camera in camera_graph.get(prev_camera, []))

        if action_ok and camera_ok:
            valid_transitions += 1

    ratio = valid_transitions / total_transitions if total_transitions > 0 else 1.0
    return weight * ratio


def _check_camera_stability(storyboard: dict, weight: float) -> float:
    """
    15分：运镜平滑性。检查是否有连续3个相同景别。
    """
    shots = storyboard.get("shots", [])
    if len(shots) < 3:
        return weight

    camera_ids = [s.get("camera_id", "") for s in shots]
    penalty = 0
    for i in range(2, len(camera_ids)):
        if camera_ids[i] == camera_ids[i-1] == camera_ids[i-2]:
            penalty += 1

    max_penalties = max(len(camera_ids) - 2, 1)
    ratio = 1.0 - (penalty / max_penalties)
    return weight * ratio


def _check_prompt_completeness(storyboard: dict, weight: float) -> float:
    """
    15分：每个 shot 的 visual_prompt 是否包含核心维度关键词。
    """
    required = ["wearing", "performing", "in ", "masterpiece"]
    shots = storyboard.get("shots", [])
    if not shots:
        return 0.0

    scores = []
    for shot in shots:
        vp = shot.get("visual_prompt", "").lower()
        hits = sum(1 for kw in required if kw in vp)
        scores.append(hits / len(required))

    avg_score = sum(scores) / len(scores)
    return weight * avg_score


def _check_hook_pose(storyboard: dict, weight: float) -> float:
    """
    10分：第一个 shot 是 hook，最后一个 shot 是 pose。
    """
    shots = storyboard.get("shots", [])
    if not shots:
        return 0.0

    score = 0.0
    if shots[0].get("type") == "hook":
        score += 0.5
    if shots[-1].get("type") == "pose":
        score += 0.5
    return weight * score


def _check_prompt_length(storyboard: dict, weight: float,
                          min_words: int = 60, max_words: int = 250) -> float:
    """
    5分：每个 shot 的 Prompt 长度在 60-250 词之间。
    """
    shots = storyboard.get("shots", [])
    if not shots:
        return 0.0

    scores = []
    for shot in shots:
        vp = shot.get("visual_prompt", "")
        wc = len(vp.split())
        if min_words <= wc <= max_words:
            scores.append(1.0)
        elif wc < min_words:
            scores.append(wc / min_words)
        else:
            scores.append(max_words / wc)

    return weight * (sum(scores) / len(scores))


def _check_diversity(storyboard: dict, weight: float, min_ratio: float = 0.6) -> float:
    """
    5分：动作多样性，不重复。
    """
    shots = storyboard.get("shots", [])
    if not shots:
        return 0.0

    action_ids = [s.get("action_id", "") for s in shots if s.get("action_id")]
    if not action_ids:
        return weight * 0.5

    ratio = len(set(action_ids)) / len(action_ids)
    return weight * (ratio / min_ratio if ratio < min_ratio else 1.0)


def _check_negative_prompt(storyboard: dict, weight: float) -> float:
    """
    5分：是否有有效 negative prompt。
    """
    np = storyboard.get("negative_prompt", "")
    if np and len(np) > 20:
        return weight
    return 0.0


# ─── 主评估函数 ───────────────────────────────────────────────────────────────
def evaluate(storyboard: Union[dict, str],
             quality_weights_path: str = None) -> dict:
    """
    对生成的 storyboard 逐项打分。
    storyboard: dict 或 JSON 文件路径
    返回: {"total_score": float, "dimension_scores": dict, "passed": bool, "issues": list}
    """
    # 支持传入文件路径
    if isinstance(storyboard, str):
        with open(storyboard, "r", encoding="utf-8") as f:
            storyboard = json.load(f)

    # 加载权重配置
    cfg = _load_quality_weights()
    dims = cfg.get("dimensions", {})
    min_pass = cfg.get("min_pass_score", 70)

    dimension_scores = {}
    issues = []

    # 逐维度评分
    w = dims.get("character_consistency", {}).get("weight", 25)
    s = _check_character_consistency(storyboard, w)
    dimension_scores["character_consistency"] = round(s, 2)
    if s < w * 0.7:
        issues.append(f"人物一致性不足: {s:.1f}/{w} — anchor_prompt 关键词覆盖率低")

    w = dims.get("temporal_continuity", {}).get("weight", 20)
    s = _check_temporal_continuity(storyboard, w)
    dimension_scores["temporal_continuity"] = round(s, 2)
    if s < w * 0.7:
        issues.append(f"帧间连续性不足: {s:.1f}/{w} — 存在非法动作/运镜过渡")

    w = dims.get("camera_stability", {}).get("weight", 15)
    s = _check_camera_stability(storyboard, w)
    dimension_scores["camera_stability"] = round(s, 2)
    if s < w * 0.7:
        issues.append(f"运镜稳定性不足: {s:.1f}/{w} — 存在连续相同景别")

    w = dims.get("prompt_completeness", {}).get("weight", 15)
    s = _check_prompt_completeness(storyboard, w)
    dimension_scores["prompt_completeness"] = round(s, 2)
    if s < w * 0.7:
        issues.append(f"Prompt 完整性不足: {s:.1f}/{w} — 缺少核心维度关键词")

    w = dims.get("hook_pose_presence", {}).get("weight", 10)
    s = _check_hook_pose(storyboard, w)
    dimension_scores["hook_pose_presence"] = round(s, 2)
    if s < w * 0.9:
        issues.append(f"Hook/Pose 结构缺失: {s:.1f}/{w} — 首帧非hook或末帧非pose")

    w = dims.get("prompt_length", {}).get("weight", 5)
    min_w = dims.get("prompt_length", {}).get("min_words", 60)
    max_w = dims.get("prompt_length", {}).get("max_words", 250)
    s = _check_prompt_length(storyboard, w, min_w, max_w)
    dimension_scores["prompt_length"] = round(s, 2)
    if s < w * 0.7:
        issues.append(f"Prompt 长度不合规: {s:.1f}/{w} — 应在{min_w}-{max_w}词之间")

    w = dims.get("diversity_score", {}).get("weight", 5)
    min_ratio = dims.get("diversity_score", {}).get("min_ratio", 0.6)
    s = _check_diversity(storyboard, w, min_ratio)
    dimension_scores["diversity_score"] = round(s, 2)
    if s < w * 0.6:
        issues.append(f"动作多样性不足: {s:.1f}/{w} — 动作重复率过高")

    w = dims.get("negative_prompt_present", {}).get("weight", 5)
    s = _check_negative_prompt(storyboard, w)
    dimension_scores["negative_prompt_present"] = round(s, 2)
    if s < w:
        issues.append(f"缺少 Negative Prompt: {s:.1f}/{w}")

    total_score = round(sum(dimension_scores.values()), 2)
    passed = total_score >= min_pass

    return {
        "total_score":       total_score,
        "max_score":         100,
        "min_pass_score":    min_pass,
        "passed":            passed,
        "dimension_scores":  dimension_scores,
        "issues":            issues
    }


def passes_threshold(storyboard: Union[dict, str], min_score: int = None) -> bool:
    """快速判断是否达到质量门禁阈值。"""
    result = evaluate(storyboard)
    threshold = min_score if min_score is not None else result["min_pass_score"]
    return result["total_score"] >= threshold


def generate_report(eval_result: dict) -> str:
    """生成人类可读的质量评估报告。"""
    lines = [
        "=" * 50,
        f"质量评估报告",
        f"总分: {eval_result['total_score']} / {eval_result['max_score']}",
        f"状态: {'✅ 通过' if eval_result['passed'] else '❌ 未通过（低于' + str(eval_result['min_pass_score']) + '分）'}",
        "-" * 50,
        "各维度得分:"
    ]
    for dim, score in eval_result["dimension_scores"].items():
        lines.append(f"  {dim}: {score}")

    if eval_result["issues"]:
        lines.append("-" * 50)
        lines.append("失分项:")
        for issue in eval_result["issues"]:
            lines.append(f"  ⚠️  {issue}")
    lines.append("=" * 50)
    return "\n".join(lines)


# ─── CLI 测试入口 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        result = evaluate(path)
    else:
        print("Usage: python quality_evaluator.py <storyboard.json>")
        exit(1)
    print(generate_report(result))
