import os
import json
import time
import sys
try:
    import readline
except ImportError:
    pass
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared_tools.config_loader import get_config

# ---------------------------------------------------------------------------
# Skill: Agent-Reach / last30days-cn — Trending Content Research
# ---------------------------------------------------------------------------
def get_trending_research(goal_text: str) -> str:
    print(f"  [Research] Mocking trending research for goal: {goal_text} to bypass sandbox blocks")
    return """=== Mocked Trending ===
1. AI 舞蹈非常火
2. 视觉钩子：美女、反差
3. BGM要动感"""

def research_trending(goal_text):
    print(f"  [Research] Mocking trending research for goal: {goal_text} to bypass sandbox blocks")
    return """=== Mocked Trending ===
1. AI 舞蹈非常火
2. 视觉钩子：美女、反差
3. BGM要动感"""

    raw_research = "\n".join(results) if 'results' in locals() and results else "暂无调研结果"
    
    if "暂无" not in raw_research:
        print("  [Research] Distilling dynamic SOP from raw research...")
        distilled = call_llm(
            "你是一个短视频爆款提炼专家。",
            f"""以下是全网最新爆款数据。请用【1句话】总结出它们共有的一个最有效、最新颖的视频结构或内容套路，作为本次创作的最高动态指导原则：
{raw_research}"""
        )
        if distilled:
            return f"""【最新趋势动态特征】: {distilled.strip()}

---
原始数据参考：
{raw_research}"""
            
    return raw_research

import random

from shared_tools.api_pool import call_llm

# ---------------------------------------------------------------------------
# Storyboard Generation (integrates video-spec-builder methodology)
# ---------------------------------------------------------------------------
def generate_storyboard(goal_text, audience, style, format_type, trending_research, feedback=None, previous_draft="", ticket=None, character="default"):
    max_vo = get_config("MAX_VOICEOVER_CHARS", "20")
    max_shot_sec = int(get_config("MAX_SHOT_DURATION_SEC", "5"))
    max_video_sec = int(get_config("MAX_VIDEO_DURATION_SEC", "60"))
    max_shots = max_video_sec // max_shot_sec
    
    language = ticket.get("language", "中文") if ticket else "中文"
    aspect_ratio = ticket.get("aspect_ratio", "9:16") if ticket else "9:16"
    
    # Load dynamic memory for Planning evolutio
    memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "company_memory.json")
    evolution_rules = ""
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            import json
            mem = json.load(f)
            pos = mem.get("positive_patterns", [])
            neg = mem.get("negative_patterns", [])
            if pos or neg:
                evolution_rules = "\n\n【自主进化规则库】（基于历史失败与CEO教训，必须严格遵守）:\n"
                if pos:
                    evolution_rules += "**[必须执行 (DO)]**\n- " + "\n- ".join(pos) + "\n"
                if neg:
                    evolution_rules += "**[绝对禁止 (DON'T)]**\n- " + "\n- ".join(neg) + "\n"
    except:
        pass
        
    # Load Marketing SOP RAG
    sop_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "marketing_sop.md")
    marketing_sop = ""
    try:
        with open(sop_path, "r", encoding="utf-8") as f:
            marketing_sop = "\n\n【行业爆款营销结构 SOP】（必选强制执行）:\n" + f.read() + "\n"
    except:
        pass

    # 分支 1: 旁白演绎 (Voiceover Branch - Strict Physics)
    if "旁白" in format_type or format_type == "Voiceover":
        system_prompt = f"""你是一个顶级的短视频广告营销导演和编剧。当前选择的分支是【旁白演绎】。
你的工作方式参考 video-spec-builder 方法论：
- 拒绝一切模糊词汇。每个镜头必须有具体可拍摄的画面描述。
- 每个 Shot 必须精确到秒，时间线严格连续。
- 画面描述必须是静态可执行的（人物站立/坐着/特写），严禁复杂物理交互（穿门、握手、奔跑）。

【🔥 旁白演绎规范 (Strict Physics)】
1. 极简物理约束：强制剥离非必要的物理交互，尽量采用静态中景/特写 (Static shot) 或平移，避免视频大模型生成“肢体变异”。
2. 场景与软件具象化：严禁使用泛泛的词汇，直接指定UI细节。
3. 提示词内嵌字卡：充分利用大模型能力生成 UI 文字标签。
4. 光影情绪反差：在各镜头间通过光影建立强烈对比。
5. 肢体动作与台词强绑定：**严禁复杂的空间指向交互或手部动作（如：指向屏幕、单手托举）**，只能使用绝对静态的姿态（如：产品静置、人物自然站立持握）。
6. TTS 情绪底层控制：旁白严禁播音腔，大量使用强情绪标点。
7. 字秒比铁律：旁白长度严格遵守每 5 秒不超过 15-18 汉字。
8. 角色一致性：每句英文 Prompt 必须重复主角外貌特征！
9. 【Agnes 官方提示词结构】Video Prompt (英文) 必须严格遵循官方结构：
   [主体] + [场景 / 环境] + [风格] + [光照] + [构图] + [质量要求]
   例如：A luminous floating city above a misty canyon at sunrise, cinematic realism, wide angle, high visual density
{evolution_rules}{marketing_sop}
以下是【爆款调研结果】：
---
{trending_research}
---

【严格格式要求】必须包含以下 Markdown 结构：
# 剧本与分镜 (Storyboard & Voiceover Blueprint)

**核心目标 (Goal)**: [目标]
**受众与风格 (Audience & Style)**: {audience} | {style}
**形式 (Format)**: {format_type}
**时长**: 约 [总时长] 秒

## 角色设定 (Characters)
- [角色1]: [特征]

## Shot 1: [标题]
**时间范围**: 0:00 - 0:0{max_shot_sec} ({max_shot_sec}s)
**场景 (Scene)**: [具体场景描述]
**图像建议 (Image Suggestion)**: [静态画面动作，确保存留安全区，不裁切头部]
**旁白 (Voiceover)**: [情绪化、口语化台词，无AI味]
**提示词 (Video Prompt)**: [英文画面描述，包含特征、字卡与 safe margins, no head cropping 等指令]"""

    elif "换装" in format_type or "变身" in format_type:
        system_prompt = f"""你是一个顶级的短视频营销导演。当前分支是【换装变身反差】。
你的工作方式参考 video-spec-builder 方法论：
- 拒绝一切模糊词汇。每个镜头必须有具体可拍摄的画面描述。
- 每个 Shot 必须精确到秒，时间线严格连续。
- 最大允许幕数 = {max_shots} 幕。

【🔥 换装变身反差规范 (Transformation Branch)】
1. 绝对无台词/旁白：这是一个纯视觉冲击的分支。**剧本中绝对不能出现任何 `台词 (Dialogue)` 或 `旁白 (Voiceover)` 字段。**
2. 强烈的视觉反差：明确定义变身前（Setup）和变身后（Reveal）的妆容、服装、光影对比。
3. 转场设计：中间必须有 Glitch（故障）或其他强视觉过渡。
4. 【Agnes 官方提示词结构】Video Prompt (英文) 必须严格遵循官方文生图/视频结构：
   [主体] + [场景 / 环境] + [风格] + [光照] + [构图] + [质量要求]
{evolution_rules}{marketing_sop}
以下是【爆款调研结果】：
---
{trending_research}
---

【严格格式要求】必须包含以下 Markdown 结构：
# 剧本与分镜 (Storyboard & Live-Action Blueprint)

**核心目标 (Goal)**: [目标]
**受众与风格 (Audience & Style)**: {audience} | {style}
**形式 (Format)**: {format_type}
**时长**: 约 [总时长] 秒

## 角色设定 (Characters)
- [角色1]: [特征，包括变身前和变身后的描述]

## Shot 1: [标题]
**时间范围**: 0:00 - 0:05 (5s)
**场景 (Scene)**: [具体场景描述]
**图像建议 (Image Suggestion)**: [静态画面动作，确保存留安全区，不裁切头部]
**提示词 (Video Prompt)**: [英文画面描述，包含特征、字卡与 safe margins 等指令]
"""

    elif "舞蹈" in format_type or "钩子" in format_type:
        # ─── Layer 4+5: Director Engine + Temporal Engine ────────────────────
        # LLM 不做任何创意决策。所有创意由 director_engine.direct() 完成。
        import sys, importlib.util

        # 动态导入 director_engine（同目录）
        _de_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "director_engine.py")
        _de_spec  = importlib.util.spec_from_file_location("director_engine", _de_path)
        _de_mod   = importlib.util.module_from_spec(_de_spec)
        _de_spec.loader.exec_module(_de_mod)

        # 解析 character_id 和 trend_id（从 goal_text 或 ticket 中提取）
        _char_id  = None
        _trend_id = None
        if ticket:
            _char_id  = ticket.get("character_id") or ticket.get("module_params", {}).get("character_id")
            _trend_id = ticket.get("trend_id")

        # 从 goal_text 智能推断热点 trend_id
        if not _trend_id:
            _goal_lower = goal_text.lower()
            if "健身" in _goal_lower or "fitness" in _goal_lower or "运动" in _goal_lower:
                _trend_id = "2026_fitness_power"
            elif "科目三" in _goal_lower:
                _trend_id = "2026_kemuzisan_viral"
            elif "国风" in _goal_lower or "汉服" in _goal_lower:
                _trend_id = "2026_guofeng_hanfu"
            elif "赛博" in _goal_lower or "cyber" in _goal_lower:
                _trend_id = "2026_cyber_dance"

        # 若未指定角色，从 goal 中匹配
        if not _char_id:
            _char_id_map = {
                "luna": "C001_Luna", "c001": "C001_Luna",
                "mika": "C002_Mika", "c002": "C002_Mika",
                "aria": "C003_Aria", "c003": "C003_Aria",
                "nyx":  "C004_Nyx",  "c004": "C004_Nyx",
                "lili": "C005_Lili", "c005": "C005_Lili",
                "yumi": "C006_Yumi", "c006": "C006_Yumi",
            }
            _goal_lower = goal_text.lower()
            for _alias, _cid in _char_id_map.items():
                if _alias in _goal_lower:
                    _char_id = _cid
                    break
            if not _char_id:
                _char_id = "C001_Luna"  # 默认角色

        # 解析目标时长
        _total_dur = 12
        if ticket:
            _total_dur = int(ticket.get("total_duration", ticket.get("duration", 12)))

        # [Task-07] 动作关键词 → motion_library ID 映射（无需 LLM）
        MOTION_KEYWORD_MAP = {
            "扭腰": "R06",   "扭胯": "R01",   "科目三": "R09",
            "甩发": "R06",   "手势舞": "R04", "hiphop": "R03",
            "hip-hop": "R03", "古风": "R10",   "袖舞": "R10",
            "慢摇": "R05",   "街舞": "R03",   "韩舞": "R07",
            "bounce": "R08", "滑步": "R08",
        }
        # [Task-07] 风格关键词 → BGM ID 映射（无需 LLM）
        STYLE_BGM_MAP = {
            "科目三": "BGM_001", "街头": "BGM_001", "hiphop": "BGM_001",
            "韩舞": "BGM_001",   "kpop": "BGM_001", "古风": "BGM_004",
            "汉服": "BGM_004",   "lo-fi": "BGM_005", "慢节奏": "BGM_005",
        }
        goal_lower = (ticket.get("goal", "") + " " + ticket.get("style", "")).lower()
        _matched_motion = next((v for k, v in MOTION_KEYWORD_MAP.items() if k in goal_lower), "R01")
        _matched_bgm    = next((v for k, v in STYLE_BGM_MAP.items() if k in goal_lower), "BGM_001")
        # Store on ticket for post-production use (non-persisted, in-memory)
        if ticket:
            ticket["_resolved_motion_id"] = _matched_motion
            ticket["_resolved_bgm_id"]    = _matched_bgm

        # ─── 调用 LLM 动态切割 Timeline ───────────────────────────────────────
        custom_beats = None
        timeline_sys_prompt = f"你是一个顶级的短片剪辑师。用户需要一个总长为 {_total_dur} 秒的动态视频。根据 V2.0 规范，单个镜头的上限为 18 秒。请你根据音乐张力和动作连贯性，自主将 {_total_dur} 秒拆分为【至少 3 个、至多 6 个】镜头（可长可短，比如 [8, 12, 10] 或 [5, 8, 7, 5, 5]）。绝对不能少于 3 个镜头。请直接返回一个由数字组成的 JSON 数组，要求总和严格等于 {_total_dur}。不要输出任何其他 Markdown 或解释文本。"
        timeline_user_prompt = f"目标：{goal_text}。总时长：{_total_dur} 秒。请输出时间分割数组："
        try:
            raw_beats = call_llm(timeline_sys_prompt, timeline_user_prompt)
            import json
            import re
            array_match = re.search(r'\[(.*?)\]', raw_beats)
            if array_match:
                custom_beats = json.loads(f"[{array_match.group(1)}]")
                if sum(custom_beats) != _total_dur:
                    print(f"  [Planning Dept] ⚠️ LLM sum {sum(custom_beats)} != {_total_dur}, using fallback.")
                    custom_beats = None
                elif len(custom_beats) < 3:
                    max_idx = custom_beats.index(max(custom_beats))
                    longest = custom_beats[max_idx]
                    half1 = round(longest / 2)
                    half2 = longest - half1
                    custom_beats[max_idx:max_idx+1] = [half1, half2]
                    print(f"  [Planning Dept] ⚠️ Beats count < 3, split longest → {custom_beats}")
        except Exception as e:
            print(f"  [Planning Dept] ⚠️ LLM duration parsing error: {e}")
            custom_beats = None

        # ─── 调用导演引擎（Layer 4+5）─────────────────────────────────────────
        if feedback:
            import random
            random.seed()
            _de_mod._CACHE.clear()
            print(f"[Planning Dept] ⚠️ QA feedback detected in dance branch, re-randomizing: {feedback[:80]}...")

        print(f"[Planning Dept] 🎬 Director Engine 启动: {_char_id}, {_total_dur}s, trend={_trend_id}")
        try:
            _decision = _de_mod.direct(_char_id, _total_dur, _trend_id, module_params=ticket.get("module_params"), custom_beats=custom_beats)
        except Exception as _de_err:
            print(f"[Planning Dept] ⚠️  Director Engine 异常: {_de_err}，使用默认参数重试")
            _decision = _de_mod.direct("C001_Luna", 12, None)

        # ─── 直接组装返回完整的结构化数据（Bypass LLM）────────────────────────
        stage_2_timeline = _decision.get("stage_2_video", {}).get("timeline", [])
        loop_pattern = _decision.get("stage_2_video", {}).get("loop_pattern", "")
        vibe = _decision.get("metadata", {}).get("vibe", "pure")
        
        speed_modifier = "moves smoothly, fluidly, elegant and graceful rhythm"
        if vibe in ["energy", "psychedelic"]:
            speed_modifier = "moves rapidly, explosively, sharp and dynamic rhythm"
        
        # 极简 Stage 2 Video Prompt 组装
        _cam_descriptions = []
        for _s in stage_2_timeline:
            _cp = _s.get("camera_prompt", "")
            if _cp:
                _cam_descriptions.append(f"shot {_s['shot']}: {_cp}")
        _camera_summary = ". ".join(_cam_descriptions) if _cam_descriptions else "Locked camera, no camera movement"
        
        stage_2_prompt = (
            f"The video begins exactly from the input image. She steps back to reveal full body, "
            f"executes the {loop_pattern} dance move. She {speed_modifier}. "
            f"Camera work: {_camera_summary}. Keep camera mostly static to focus on the dance, avoid extreme panning or rapid zooming. "
            f"Spend the last 2 seconds smoothly returning limbs and body to the exact interactive anchor pose from the first frame, locking into it perfectly for seamless loop. "
            f"Constant intense eye contact with the viewer throughout the entire video. "
            f"Consistent facial features and expressions, no face morphing. "
            f"Consistent clothing, outfit remains exactly the same throughout the entire video, no clothing changes."
        )
        
        task_data = {
            "ticket_id": ticket.get("id") if ticket else "UNKNOWN",
            "goal": ticket.get("goal") if ticket else "",
            "total_duration": _total_dur,
            "character": _decision.get("character_id"),
            "stage_1_image": _decision.get("stage_1_image", {}),
            "stage_2_video": {
                "loop_pattern": loop_pattern,
                "timeline": stage_2_timeline,
                "video_prompt": stage_2_prompt
            },
            "metadata": _decision.get("metadata", {})
        }
        
        # Mock LLM JSON output format to satisfy downstream parsers if needed
        return f"```json\n{__import__('json').dumps(task_data, indent=2, ensure_ascii=False)}\n```"


    else:
        system_prompt = f"""你是一个顶级的短视频广告营销导演和编剧。当前选择的分支是【真人剧场情景】。
你的工作方式参考 video-spec-builder 方法论：
- 拒绝一切模糊词汇。每个镜头必须有具体可拍摄的画面描述。
- 每个 Shot 必须精确到秒，时间线严格连续。
- 最大允许幕数 = {max_shots} 幕。请根据故事节奏自行决定具体幕数（如只需3幕，或可达{max_shots}幕），严禁固定套用4幕模板！
- **全局语言要求**: 剧本的台词、画面字卡 (Text Overlay)、场景描述必须全部使用【{language}】。

【🔥 图像与视频构图铁律 (Safe Margins & Cropping)】
1. 必须在画面四周留出安全区 (leave safe margins for text)，防止文字截断。
2. 确保人物头部完整不被裁切 (do not crop head)。
3. 在生成 Video Prompt 时，必须加入构图保护指令。

【🔥 真人剧场规范 (Live-Action Scenario)】
1. 连贯情节与微表情：侧重面部情绪与微表情传递。**严禁复杂的物理互动与大范围走位（绝对不要写：转身、递东西、奔跑、复杂的手部交互）**，只能使用安全的静态微小姿态（如：静止站立、手持产品、头部微侧）。
2. 实景拍摄感：画面描述侧重于镜头语言（如手持摇晃跟拍 Handheld tracking shot、大特写 Extreme close-up）。
3. 场景与软件具象化：直接指定道具细节。
4. 光影情绪反差：营造电影级打光。
5. 台词与人物冲突：设计激烈的双人对话或戏剧冲突。
6. 字秒比铁律：每一句台词文本的总字符数（严格包含标点符号）必须绝对小于等于 {max_vo} 个字！
7. 角色一致性：每句英文 Prompt 必须重复所有出场人物的外貌特征！
8. 核心产品出镜铁律：营销目标的核心产品必须在画面中清晰出现，绝对不能遗漏核心道具。
9. 【Agnes 官方提示词结构】Video Prompt (英文) 必须严格遵循官方文生图/视频结构：
   [主体] + [场景 / 环境] + [风格] + [光照] + [构图] + [质量要求]
   例如：A luminous floating city above a misty canyon at sunrise, cinematic realism, wide angle, high visual density
{evolution_rules}{marketing_sop}
以下是【爆款调研结果】：
---
{trending_research}
---

【严格格式要求】必须包含以下 Markdown 结构：
# 剧本与分镜 (Storyboard & Live-Action Blueprint)

**核心目标 (Goal)**: [目标]
**受众与风格 (Audience & Style)**: {audience} | {style}
**形式 (Format)**: {format_type}
**时长**: 约 [总时长] 秒

## 角色设定 (Characters)
- [角色1]: [特征]
- [角色2]: [特征]

## Shot 1: [标题]
**时间范围**: 0:00 - 0:0{max_shot_sec} ({max_shot_sec}s)
**场景 (Scene)**: [具体场景描述]
**图像建议 (Image Suggestion)**: [绝对静态的画面特征描述，禁用任何动态动词，确保存留安全区，不裁切头部]
**台词 (Dialogue)**: [口语化角色对白/内心OS，无AI味]
**提示词 (Video Prompt)**: [绝对静态的英文画面描述，禁止任何动态交互动词，包含全员外貌特征，以及 safe margins 指令]

(按故事需要自由增加 Shot 2, Shot 3... 最高可达 {max_shots} 幕)
"""

    user_prompt = f"""营销目标：{goal_text}
目标受众：{audience}
期望风格：{style}
"""
    if previous_draft:
        user_prompt += f"""
【上一次生成的草稿剧本 (Previous Draft)】：
{previous_draft}
"""

    if feedback:
        user_prompt += (
            f"""

<CRITICAL_CORRECTION>
🚨 质检部门(QA) 已将上一版剧本打回！你必须立即修正以下严重错误 🚨
【QA 审核反馈】:
{feedback}

【强制执行指令】:
1. 仔细阅读上方 QA 反馈指出的违规点（例如：包含了动态词汇、复杂动作等）。
2. 如果 QA 在反馈中给出了修改建议的示例（例如建议改为纯静态姿态描述如“呈现邀请手势”、“头部呈后仰角度”，或建议移除相机指令），你必须【原封不动地采纳该具体字眼】，严禁自己试图换词或重新发挥，以免再次触发 QA 误判！
3. 绝对服从 QA 部门的指导，彻底消除违规词汇，如果再次违规将导致系统死锁！
</CRITICAL_CORRECTION>
"""
        )


    # 非舞蹈分支：调用 Quality Evaluator 门禁，最多重试 3 次
    import json as _json_mod, importlib.util as _ilu

    # 动态导入 quality_evaluator（同目录）
    _qe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quality_evaluator.py")
    try:
        _qe_spec = _ilu.spec_from_file_location("quality_evaluator", _qe_path)
        _qe_mod  = _ilu.module_from_spec(_qe_spec)
        _qe_spec.loader.exec_module(_qe_mod)
        _qe_available = True
    except Exception as _qe_load_err:
        print(f"[Planning Dept] ⚠️  Quality Evaluator 加载失败: {_qe_load_err}，跳过门禁")
        _qe_available = False

    _max_attempts = 3
    _best_result  = None
    _best_score   = -1

    for _attempt in range(1, _max_attempts + 1):
        _raw_result = call_llm(system_prompt, user_prompt)
        if not _raw_result:
            print(f"[Planning Dept] ⚠️  LLM 返回为空 (attempt {_attempt})")
            continue

        if not _qe_available:
            return _raw_result

        # 尝试解析 JSON 评估
        try:
            _json_str = _raw_result
            if "```json" in _json_str:
                _json_str = _json_str.split("```json")[-1].split("```")[0].strip()
            elif "```" in _json_str:
                _json_str = _json_str.split("```")[-2].strip()
            _storyboard = _json_mod.loads(_json_str)

            _eval = _qe_mod.evaluate(_storyboard)
            _score = _eval.get("total_score", 0)
            print(f"[Planning Dept] 📊 Quality Score (attempt {_attempt}): {_score}/100 "
                  f"({'✅ PASS' if _eval.get('passed') else '❌ FAIL'})")

            if _score > _best_score:
                _best_score  = _score
                _best_result = _raw_result

            if _eval.get("passed"):
                print(f"[Planning Dept] ✅ 质量门禁通过，Score={_score}")
                return _raw_result

            # 未通过：把失分项作为反馈注入下一次重试
            if _attempt < _max_attempts:
                _issues_text = "\n".join(_eval.get("issues", []))
                user_prompt += (
                    f"\n\n<QUALITY_GATE_FEEDBACK attempt={_attempt}>\n"
                    f"Quality Score: {_score}/100 (below threshold, retry required)\n"
                    f"Issues to fix:\n{_issues_text}\n"
                    f"</QUALITY_GATE_FEEDBACK>"
                )

        except Exception as _parse_err:
            print(f"[Planning Dept] ⚠️  Quality Evaluator 解析失败 (attempt {_attempt}): {_parse_err}")
            _best_result = _raw_result

    # 3 次重试后返回最佳结果
    print(f"[Planning Dept] ⚠️  质量门禁未通过，返回最高分结果 (best_score={_best_score})")
    return _best_result if _best_result else call_llm(system_prompt, user_prompt)


def humanize_storyboard(storyboard_md, qa_feedback=""):
    """
    独立洗稿模块：利用 qu-ai-wei 技能打磨台词和旁白
    """
    import re
    # 尝试读取本地的 qu-ai-wei 技能文件
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parent_workspace_dir = os.path.dirname(workspace_dir)
    skill_path = os.path.join(parent_workspace_dir, ".agents", "skills", "qu_ai_wei", "SKILL.md")
    skill_content = ""
    try:
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                skill_content = f.read()
    except Exception as e:
        print(f"[Planning Dept] Failed to read qu-ai-wei skill: {e}")

    if not skill_content:
        return storyboard_md # 若没有技能文件则跳过

    print("[Planning Dept] 正在调用去AI味 (qu-ai-wei) 技能进行台词后处理...")

    from shared_tools.config_loader import get_config
    max_vo = get_config("MAX_VOICEOVER_CHARS", "20")

    system_prompt = f"""你是一个顶级的短剧台词编辑。
这是你的核心打磨技能指南 (qu-ai-wei)：
---
{skill_content[:3000]} # 截取前3000字以防超出Toke
---
你的任务是：
1. 提取以下剧本中所有的【旁白 (Voiceover)】和【台词 (Dialogue)】。
2. 使用 qu-ai-wei 技能规则将它们重写，彻底去除 AI 塑料味，保留碎片化、口语化的真人质感。
3. 请只修改文本中的旁白和台词部分，原样输出其余的剧本结构、镜头描述、时间等。必须保持 Markdown 格式完全不变！
4. 【死线纪律】重写后的每句旁白/台词**绝对不能超过 {max_vo} 个汉字（含标点符号）**！如果超过，语音系统会截断报错。必须精简到极致！
5. 【格式红线】请直接用修改后的纯文本替换原内容！**绝对禁止**输出任何解释、分析、字数统计、或“-> 修正后”等标记。行内只能保留最终要发音的纯文本。
"""
    if qa_feedback:
        system_prompt += f"\n🚨 质检部门(QA) 前次打回反馈:\n{qa_feedback}\n请务必在洗稿时严格规避以上违规点！\n"

    humanized_md = call_llm(system_prompt, f"请原样返回以下剧本结构，但彻底洗稿里面的旁白/台词：\n\n{storyboard_md}")
    return humanized_md if humanized_md else storyboard_md

import concurrent.futures
import importlib.util

def run_requirements_gathering(ticket):
    """
    Conducts interactive requirements gathering.
    Uses concurrent fetching for research and LLM advice.
    Runs a concurrent QA monitor on the chat.
    """
    print(f"\n{'='*50}")
    print(f"🎬 策划总监模式 (Interactive Requirements Gathering)")
    print(f"{'='*50}")
    print(f"收到您的初始目标：{ticket.get('goal')}\n")
    
    try:
        qa_agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "04_qa_evolution", "qa_agent.py")
        spec = importlib.util.spec_from_file_location("qa_agent", qa_agent_path)
        qa_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qa_agent)
    except Exception as e:
        print(f"[QA Load Error] {e}")

    try:
        from shared_tools.skill_engine import SkillEngine
        skill_engine = SkillEngine()
    except Exception as e:
        print(f"[SkillEngine Load Error] {e}")
        skill_engine = None

    print("[Planning Dept] 正在并发执行全网爆款调研与初步方案构思...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_research = executor.submit(research_trending, ticket.get('goal'))
        
        selected_branch = ticket.get("selected_branch", "AI舞蹈与视觉钩子")
        future_style = executor.submit(
            call_llm,
            f"你是一个顶级的短视频营销导演。用户已经选择了【{selected_branch}】这一展现形式。请基于用户目标，提供风格分析和受众建议，并询问用户是否需要特定的『角色IP』(如Goth Girl, 健身教练等)。语气专业直接，提问引导用户。",
            f"营销目标：{ticket.get('goal')}\n形式：{selected_branch}\n请给出建议，并询问用户意向。"
        )
        trending_research = future_research.result()
        initial_advice = future_style.result()
    
    # Save trending research to ticket immediately
    ticket["trending_research"] = trending_research

    print("\n[CEO] 请与策划总监讨论您的想法 (输入 'ok'、'确认' 结束讨论，直接进入生成)：")
    
    chat_history = [
        {"role": "assistant", "content": initial_advice}
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        while True:
            web_project_id = os.environ.get("CURRENT_WEB_PROJECT_ID")
            
            if web_project_id:
                print(f"[AWAITING_USER_INPUT] {web_project_id}", flush=True)
                import requests
                user_input = "ok"
                ports = [os.environ.get("BACKEND_PORT", ""), "8000", "8008"]
                for p in filter(None, dict.fromkeys(ports)):
                    try:
                        resp = requests.get(f"http://localhost:{p}/api/projects/{web_project_id}/internal_wait_input", timeout=86400)
                        if resp.status_code == 200:
                            user_input = resp.json().get("text", "ok")
                            break
                    except Exception:
                        continue

            else:
                import sys as _sys
                # Non-interactive mode: stdin is a pipe, auto-confirm
                if not _sys.stdin.isatty():
                    print("[Auto-Mock] Non-TTY stdin detected. Auto-confirming 'ok'.")
                    user_input = "ok"
                else:
                    try:
                        user_input = input("\n您 > ")
                    except EOFError:
                        print("[Auto-Mock] EOFError detected. Typing 'ok'.")
                        user_input = "ok"
                
            lower_input = user_input.strip().lower()
            exit_keywords = ['ok', 'confirm', '确认', '好了', '可以了', '生成', 'pass', '是的', '执行']
            
            # Check if it exactly matches or starts with simple exit words
            if lower_input in exit_keywords or lower_input.startswith('ok') or lower_input.startswith('确认'):
                break
                
            # Check for explicit commands to move forward in a sentence
            if any(k in lower_input for k in ['进入下一步', '开始输出', '开始执行', '开始生成', '不用再增加']):
                break
                
            chat_history.append({"role": "user", "content": user_input})
            
            # --- Concurrent QA Monitoring ---
            qa_future = None
            if qa_agent:
                full_history = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
                qa_future = executor.submit(qa_agent.audit_chat_context, full_history)
                
            # We must wait for QA to finish to inject its feedback if needed
            qa_warning = ""
            if qa_future:
                passed, msg = qa_future.result()
                if not passed:
                    qa_warning = f"\n【QA Monitor 紧急打回警告】: {msg}"
            
            system_instruction = f"你是一个顶级短视频营销导演。正与CEO探讨策划方向，已锁定分支为【{ticket.get('selected_branch', 'AI舞蹈与视觉钩子')}】，重点确认【受众】、【风格】与【角色IP】。保持简短精炼。"
            if qa_warning:
                system_instruction += qa_warning
            
            if skill_engine:
                reply = skill_engine.run_agentic_loop(system_instruction, chat_history, call_llm)
            else:
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-6:]])
                reply = call_llm(system_instruction, history_text)
            
            if not reply:
                print("\n🤖 [AI 策划总监]：(抱歉，API连接失败。)")
            else:
                print(f"\n🤖 [AI 策划总监]：{reply}")
                chat_history.append({"role": "assistant", "content": reply})

    print("\n[Planning Dept] 正在总结您的最终需求...")
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    summary = call_llm(
        "你是一个助手，请从以下对话记录中，提取用户最终敲定的【目标受众】、【视频风格】和【角色IP（如果没有则为 default）】。",
        f"目标主题：{ticket.get('goal')}\n对话记录：\n{history_text}\n请严格按照此格式输出：\nAudience: XXX\nStyle: XXX\nCharacter: XXX\n如果对话中没有明确指出，请基于讨论内容自己推理。"
    )
    
    audience = "通用受众"
    style = "高级感营销"
    format_type = ticket.get("selected_branch", "AI舞蹈与视觉钩子")
    character = "default"
    
    if summary:
        for line in summary.split('\n'):
            if line.startswith("Audience:"):
                audience = line.replace("Audience:", "").strip()
            elif line.startswith("Style:"):
                style = line.replace("Style:", "").strip()
            elif line.startswith("Character:"):
                character = line.replace("Character:", "").strip()
                
    print(f"[Planning Dept] 需求锁定 - Audience: {audience} | Style: {style} | Format: {format_type} | Character: {character}")
    
    # Save to a requirements.json file just to have an explicit contract artifact
    req_path = os.path.join(os.path.dirname(ticket.get("goal", "a")), "00_requirements.json")
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            json.dump({"audience": audience, "style": style, "format": format_type, "character": character, "chat_summary": summary}, f, ensure_ascii=False, indent=2)
    except:
        pass
        
    return audience, style, format_type, character

# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------
def process_ticket(episode_dir):
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")

    if not os.path.exists(ticket_path):
        print(f"[Planning Dept] No task ticket found in {episode_dir}")
        return False

    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)

    if ticket.get("status") not in ["Pending", "Requirements_Gathering", "Drafting"]:
        print(f"[Planning Dept] Ticket status is {ticket.get('status')}. Ignoring.")
        return False

    print(f"\n[Planning Dept] Processing ticket: {ticket.get('goal')}")

    # ── Phase 0: Market Research (Agent-Reach / last30days-cn) ──
    trending_research = ticket.get("trending_research", "")
    if "作为AI助手" in trending_research:
        print("[Planning Dept] Invalidating bad cached research (AI refusal detected).")
        trending_research = ""

    if not trending_research and ticket.get("status") != "Pending" and ticket.get("status") != "Requirements_Gathering":
        pass
    elif trending_research:
        print("[Planning Dept] Using cached trending research.")

    # ── Phase 1: Director Interview (Requirements Gathering) ──
    if ticket.get("status") in ["Pending", "Requirements_Gathering"] or not ticket.get("director_confirmed"):
        audience, style, format_type, character = run_requirements_gathering(ticket)
        ticket["director_confirmed"] = True
        ticket["audience"] = audience
        ticket["style"] = style
        ticket["format_type"] = format_type
        ticket["character"] = character
        ticket["status"] = "Drafting"
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
        print("[Planning Dept] Director confirmation saved to disk. Handing over to Drafting state.")
        return True
    else:
        audience = ticket.get("audience")
        style = ticket.get("style")
        format_type = ticket.get("format_type", "旁白演绎")
        character = ticket.get("character", "default")
        print(f"[Planning Dept] Using existing confirmed requirements: Audience={audience}, Style={style}, Format={format_type}, Character={character}")

    # ── Phase 2: LLM Storyboard Generation ──
    qa_feedback = ticket.get("qa_feedback")
    
    scripts_dir = os.path.join(episode_dir, "01_storyboards_scripts")
    script_path = os.path.join(scripts_dir, "01_storyboard.md")
    previous_draft = ""
    if qa_feedback and os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            previous_draft = f.read()

    print(f"[Planning Dept] Generating storyboard via LLM... Branch: {format_type}")
    storyboard_content = generate_storyboard(
        ticket.get("goal"), audience, style, format_type, trending_research, qa_feedback, previous_draft, ticket
    )

    if not storyboard_content:
        print("[Planning Dept] 🚨 LLM 接口调用失败 (可能因为 503 宕机或达到速率限制)。为防止死锁，将暂停任务。")
        ticket["status"] = "Paused_By_Error"
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
        return False

    # ── Phase 2.5: Script Humanization (去AI味洗稿) ──
    # 舞蹈/换装流 (Branch 3/4) 不包含台词，且输出纯 JSON，跳过洗稿以防破坏 JSON 结构
    is_dance = "舞蹈" in format_type or "钩子" in format_type or "换装" in format_type or "变身" in format_type
    if not is_dance:
        storyboard_content = humanize_storyboard(storyboard_content, qa_feedback)

    # ── Phase 3: Save storyboard ──
    scripts_dir = os.path.join(episode_dir, "01_storyboards_scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    script_path = os.path.join(scripts_dir, "01_storyboard.md")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(storyboard_content)

    print(f"[Planning Dept] Storyboard generated at {script_path}")

    ticket["qa_feedback"] = ""
    ticket["status"] = "QA_Pending_Planning"
    ticket["last_updated_by"] = "Planning_Agent"
    ticket["last_updated_time"] = time.time()
    
    # [Task-04/05] Extract and save distribution data — with guaranteed fallback from director engine
    dist_path = os.path.join(scripts_dir, "01_distribution.json")
    _dist_saved = False
    try:
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', storyboard_content, re.DOTALL)
        json_content = json_match.group(1) if json_match else storyboard_content
        parsed_data = json.loads(json_content)
        if "distribution" in parsed_data:
            with open(dist_path, "w", encoding="utf-8") as df:
                json.dump(parsed_data["distribution"], df, ensure_ascii=False, indent=2)
            print(f"  [Planning Dept] Saved distribution metadata to {dist_path}")
            _dist_saved = True
    except Exception as e:
        print(f"  [Planning Dept] Warning: Could not parse distribution metadata from storyboard: {e}")

    # [Task-04] GUARANTEED FALLBACK: If distribution.json not yet saved, generate from director engine / keyword maps
    if not _dist_saved:
        _bgm_id   = ticket.get("_resolved_bgm_id", "BGM_001")
        _goal_text = ticket.get("goal", "")
        _style_text = ticket.get("style", "")
        _hashtags = [f"#{w}" for w in [_style_text, "舞蹈", "短视频"] if w]
        _fallback_dist = {
            "bgm_id": _bgm_id,
            "cover_frame_sec": 3.2,
            "highlight_clips": ["shot_02", "shot_03"],
            "platform_tags": _hashtags,
            "_generated_by": "planning_agent_fallback"
        }
        with open(dist_path, "w", encoding="utf-8") as df:
            json.dump(_fallback_dist, df, ensure_ascii=False, indent=2)
        print(f"  [Planning Dept] ✅ Fallback distribution.json generated (bgm={_bgm_id}) at {dist_path}")
        
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)

    print("[Planning Dept] Ticket status updated to QA_Pending_Planning. Handing over to QA Dept.")
    return True


def generate_marketing_recap(run_dir: str, output_file: str = None) -> dict:
    """Extract key highlights, dramatic conflicts and CTA from a finished drama run to produce a marketing explainer script."""
    run_dir = os.path.abspath(run_dir)
    ticket_path = os.path.join(run_dir, "00_task_ticket.json")
    storyboard_path = os.path.join(run_dir, "01_storyboards_scripts", "01_storyboard.md")
    
    goal = "AI短剧精选"
    if os.path.exists(ticket_path):
        try:
            with open(ticket_path, "r", encoding="utf-8") as f:
                t = json.load(f)
                goal = t.get("goal", goal)
        except Exception:
            pass

    storyboard_text = ""
    if os.path.exists(storyboard_path):
        try:
            with open(storyboard_path, "r", encoding="utf-8") as f:
                storyboard_text = f.read()[:1000]
        except Exception:
            pass

    prompt = f"""你是一个短剧爆款宣发专家。请根据以下短剧主题与剧本大纲，写一段 30-45 秒的短视频宣发解说文案（用于数字人口播+视频切片包装）。
文案结构要求：
1. 黄金前3秒爆点钩子（如“千万别在深夜看这部剧！”或“家人们，反转太刺激了！”）
2. 核心剧情冲突与高光看点提炼（2-3句话，紧凑刺激）
3. 强力引导追剧 CTA（如“关注我看全集完整版！”）

短剧主题：{goal}
剧本节选：
{storyboard_text if storyboard_text else "精彩反转剧情，扣人心弦。"}

请直接输出纯文案内容，不要包含分镜头标记或多余说明。"""

    recap_text = ""
    try:
        recap_text = call_llm("你是一个顶尖的影视短视频宣发策划大师。", prompt)
    except Exception as e:
        print(f"  [Planning Dept] LLM generation fallback: {e}")

    if not recap_text or len(recap_text.strip()) < 10:
        recap_text = f"家人们谁懂啊！今天推荐的这部短剧《{goal}》简直绝了！全程高能无尿点，反转不断，剧情刺激到让人停不下来！想看大结局的赶紧点赞关注，带你一口气刷全集！"

    recap_text = recap_text.strip()
    result = {
        "title": f"Marketing_{os.path.basename(run_dir)}",
        "text": recap_text,
        "source_run_dir": run_dir,
        "timestamp": time.time(),
    }

    if not output_file:
        output_file = os.path.join(run_dir, "01_storyboards_scripts", "marketing_recap_script.json")

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  [Planning Dept] 📣 宣发解说文案已生成并保存至: {output_file}")
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_dir = sys.argv[1]
    else:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_dir = os.path.join(workspace_dir, "projects", "paperai-series", "episode-01")
    process_ticket(run_dir)

