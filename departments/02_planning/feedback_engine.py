"""
feedback_engine.py — Layer 9 (Feedback Engine)
Branch 3 舞蹈流专属。将平台数据回流，自动更新 rules.json 权重。
采用 JSONL 格式追加写入，永不丢失历史数据。
"""

import json
import os
import shutil
from datetime import datetime, timezone
from statistics import mean
from typing import Optional

# ─── 路径配置 ──────────────────────────────────────────────────────────────────
_DANCE_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "../../assets/dance")
_FEEDBACK_LOG_PATH = os.path.join(_DANCE_ASSETS_DIR, "feedback_log.jsonl")
_RULES_PATH = os.path.join(_DANCE_ASSETS_DIR, "rules.json")

# ─── 安全护栏 ──────────────────────────────────────────────────────────────────
WEIGHT_MIN = 0.05   # 任何单项权重不低于此值（防止过拟合到单一风格）
WEIGHT_MAX = 0.80   # 任何单项权重不高于此值（保持多样性）
MIN_SAMPLES = 3     # 至少此数量样本才进行权重更新


# ─── 记录视频发布结果 ─────────────────────────────────────────────────────────
def log_video_result(
    video_id: str,
    character_id: str,
    style_id: str,
    scene_id: str,
    hook_id: str,
    pose_id: str,
    trend_id: str,
    shot_template_id: str,
    rhythm_id: str,
    duration: int,
    platform: str,
    views: int,
    likes: int,
    completion_rate: float,
    comments: int = 0,
    shares: int = 0,
    quality_score: float = 0.0,
    log_path: str = None
) -> dict:
    """
    将一条视频的效果数据追加到 feedback_log.jsonl。
    所有字段均为必填，以保证分析时数据完整。
    """
    record = {
        "video_id":        video_id,
        "character":       character_id,
        "style":           style_id,
        "scene":           scene_id,
        "hook":            hook_id,
        "pose":            pose_id,
        "trend":           trend_id,
        "shot_template":   shot_template_id,
        "rhythm":          rhythm_id,
        "duration":        duration,
        "platform":        platform,
        "views":           views,
        "likes":           likes,
        "completion_rate": round(float(completion_rate), 4),
        "comments":        comments,
        "shares":          shares,
        "quality_score":   round(float(quality_score), 2),
        "timestamp":       datetime.now(timezone.utc).isoformat()
    }

    target_path = log_path or _FEEDBACK_LOG_PATH
    with open(target_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


# ─── 读取历史反馈 ─────────────────────────────────────────────────────────────
def load_feedback_log(log_path: str = None) -> list:
    """读取所有历史反馈记录，返回 list[dict]。"""
    target_path = log_path or _FEEDBACK_LOG_PATH
    records = []
    if not os.path.exists(target_path):
        return records
    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


# ─── 分析反馈数据 ─────────────────────────────────────────────────────────────
def analyze_feedback(log_path: str = None, min_samples: int = MIN_SAMPLES) -> dict:
    """
    分析历史数据，统计各维度组合的平均效果指标。
    返回: {
        "by_character_style": {(char, style): {avg_completion, avg_views, count}},
        "by_hook": {hook_id: {...}},
        "by_pose": {pose_id: {...}},
        "by_shot_template": {template_id: {...}},
        "hot_combos": [top N 完播率最高的组合],
        "total_records": int
    }
    """
    records = load_feedback_log(log_path)
    if not records:
        return {"total_records": 0, "by_character_style": {},
                "by_hook": {}, "by_pose": {}, "by_shot_template": {}, "hot_combos": []}

    # --- 按角色+风格聚合 ---
    char_style_data: dict = {}
    for r in records:
        key = (r.get("character", ""), r.get("style", ""))
        if key not in char_style_data:
            char_style_data[key] = {"views": [], "completion_rate": [], "likes": []}
        char_style_data[key]["views"].append(r.get("views", 0))
        char_style_data[key]["completion_rate"].append(r.get("completion_rate", 0))
        char_style_data[key]["likes"].append(r.get("likes", 0))

    by_char_style = {}
    for key, data in char_style_data.items():
        count = len(data["views"])
        by_char_style[f"{key[0]}|{key[1]}"] = {
            "character":       key[0],
            "style":           key[1],
            "count":           count,
            "avg_completion":  round(mean(data["completion_rate"]), 4) if data["completion_rate"] else 0,
            "avg_views":       round(mean(data["views"]), 0) if data["views"] else 0,
            "avg_likes":       round(mean(data["likes"]), 0) if data["likes"] else 0,
            "sufficient":      count >= min_samples
        }

    # --- 按 hook 聚合 ---
    def _group_by_field(records, field):
        agg = {}
        for r in records:
            k = r.get(field, "unknown")
            if k not in agg:
                agg[k] = {"views": [], "completion_rate": []}
            agg[k]["views"].append(r.get("views", 0))
            agg[k]["completion_rate"].append(r.get("completion_rate", 0))
        return {
            k: {
                "count": len(v["views"]),
                "avg_completion": round(mean(v["completion_rate"]), 4) if v["completion_rate"] else 0,
                "avg_views": round(mean(v["views"]), 0) if v["views"] else 0,
                "sufficient": len(v["views"]) >= min_samples
            } for k, v in agg.items()
        }

    # --- Top N 完播率组合 ---
    hot_combos = sorted(
        [v for v in by_char_style.values() if v["sufficient"]],
        key=lambda x: x["avg_completion"] * 0.6 + min(x["avg_views"] / 100000, 1.0) * 0.4,
        reverse=True
    )[:5]

    return {
        "total_records":       len(records),
        "by_character_style":  by_char_style,
        "by_hook":             _group_by_field(records, "hook"),
        "by_pose":             _group_by_field(records, "pose"),
        "by_shot_template":    _group_by_field(records, "shot_template"),
        "hot_combos":          hot_combos
    }


# ─── 自动更新权重 ─────────────────────────────────────────────────────────────
def _normalize_weights(weights: dict) -> dict:
    """归一化权重，并强制上下限。"""
    # 应用护栏
    for k in weights:
        weights[k] = max(WEIGHT_MIN, min(WEIGHT_MAX, weights[k]))
    # 归一化
    total = sum(weights.values())
    if total > 0:
        for k in weights:
            weights[k] = round(weights[k] / total, 4)
    return weights


def update_weights(rules_path: str = None, analysis_result: dict = None,
                   log_path: str = None, dry_run: bool = False) -> dict:
    """
    根据反馈分析结果自动调整 rules.json 中的 preferred_styles 权重。
    每次调整前自动备份 rules.json.bak。
    dry_run=True 时只返回计算结果，不写入文件。
    """
    target_rules_path = rules_path or _RULES_PATH
    if analysis_result is None:
        analysis_result = analyze_feedback(log_path)

    if analysis_result["total_records"] == 0:
        return {"status": "no_data", "message": "没有足够的反馈数据，权重未更新"}

    # 读取当前 rules
    with open(target_rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    by_char_style = analysis_result.get("by_character_style", {})
    changes = {}

    for char_id, char_rules in rules.items():
        if char_id.startswith("_"):
            continue

        preferred_styles = char_rules.get("preferred_styles", {})
        if not preferred_styles:
            continue

        new_weights = dict(preferred_styles)
        updated = False

        for style_id in preferred_styles:
            key = f"{char_id}|{style_id}"
            if key not in by_char_style:
                continue
            data = by_char_style[key]
            if not data.get("sufficient"):
                continue  # 样本不足，跳过

            # 效果分数 = 完播率 * 0.6 + 标准化播放量 * 0.4
            max_views = max((v["avg_views"] for v in by_char_style.values()), default=1)
            normalized_views = data["avg_views"] / max(max_views, 1)
            performance_score = data["avg_completion"] * 0.6 + normalized_views * 0.4

            # 权重调整公式：好的内容提权，差的内容降权
            current = preferred_styles[style_id]
            adjustment = 0.7 + 0.6 * performance_score  # 范围 [0.7, 1.3]
            new_weights[style_id] = current * adjustment
            updated = True

        if updated:
            new_weights = _normalize_weights(new_weights)
            changes[char_id] = {
                "before": dict(preferred_styles),
                "after":  new_weights
            }
            if not dry_run:
                rules[char_id]["preferred_styles"] = new_weights

    if not dry_run and changes:
        # 备份原文件
        backup_path = target_rules_path + ".bak"
        shutil.copy2(target_rules_path, backup_path)
        # 写入更新
        with open(target_rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)

    return {
        "status":   "updated" if (changes and not dry_run) else ("dry_run" if dry_run else "no_change"),
        "changes":  changes,
        "total_records": analysis_result["total_records"]
    }


# ─── 获取最佳组合 ─────────────────────────────────────────────────────────────
def get_hot_combos(top_n: int = 5, log_path: str = None) -> list:
    """返回历史数据中效果最佳的角色+风格组合 Top-N。"""
    analysis = analyze_feedback(log_path)
    return analysis.get("hot_combos", [])[:top_n]


# ─── CLI 入口 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "analyze"

    if cmd == "analyze":
        result = analyze_feedback()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "update":
        dry = "--dry-run" in sys.argv
        result = update_weights(dry_run=dry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("changes"):
            print(f"\n✅ 权重{'(dry-run)' if dry else ''}更新了 {len(result['changes'])} 个角色")
        else:
            print("\n⚠️  没有变更（数据不足或无改善空间）")

    elif cmd == "hot_combos":
        combos = get_hot_combos()
        print(json.dumps(combos, indent=2, ensure_ascii=False))

    elif cmd == "log":
        # 快速录入一条测试记录
        print("录入测试记录...")
        rec = log_video_result(
            video_id="TEST_001",
            character_id="C001_Luna",
            style_id="kpop_studio",
            scene_id="sunlight_studio",
            hook_id="face_closeup_stare",
            pose_id="finger_heart",
            trend_id="2026_kpop_fastcut",
            shot_template_id="tiktok_classic",
            rhythm_id="kpop_12s",
            duration=12,
            platform="tiktok",
            views=10000,
            likes=500,
            completion_rate=0.75,
            quality_score=82.0
        )
        print(json.dumps(rec, indent=2, ensure_ascii=False))

    else:
        print(f"Usage: python feedback_engine.py [analyze|update|hot_combos|log]")
