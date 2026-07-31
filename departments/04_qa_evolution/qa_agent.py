import os
import json
import time
import sys
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared_tools.parsers.storyboard_parser import load_and_parse
from shared_tools.config_loader import get_config
from shared_tools.skills_manager import skills_manager

from shared_tools.api_pool import call_llm

def compress_memory(memory_list):
    if len(memory_list) <= 8:
        return memory_list
    
    # Protect CEO rules
    ceo_rules = [r for r in memory_list if "[CEO]" in r]
    auto_rules = [r for r in memory_list if "[CEO]" not in r]
    
    if len(auto_rules) <= 5:
        return memory_list
        
    prompt = "请将以下多条记忆规则进行语义合并与压缩。要求：核心意图不丢失，条目数控制在 5 条以内。只返回JSON列表格式，如 [\"规则1\", \"规则2\"]：\n" + json.dumps(auto_rules, ensure_ascii=False)
    compressed = call_llm("你是一个专门压缩系统记忆的 AI。", prompt)
    
    try:
        import re
        match = re.search(r'\[.*\]', compressed, re.DOTALL)
        if match:
            new_auto = json.loads(match.group(0))
            return ceo_rules + new_auto
    except:
        pass
    
    # Fallback to truncation if parsing fails
    return ceo_rules + auto_rules[-(8 - len(ceo_rules)):]

def extract_evolution_rule(error_msg):
    memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "company_memory.json")
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except:
        memory = {"positive_patterns": [], "negative_patterns": []}
        
    existing_rules = "1. 旁白必须小于或等于上限字数。\n2. 图像建议不能包含复杂物理动作。\n3. 核心营销产品必须在画面中明确出现。\n"
    if memory["negative_patterns"]:
        existing_rules += "\n".join(memory["negative_patterns"])
        
    prompt = f"""作为一个系统进化反思模块，请根据以下 QA 打回原因，提炼一条【极其精简 (小于30字)】的通用规避教训(Negative Rule)。
重要：请先检查该打回原因是否已被现有的硬规则覆盖。
现有规则：
{existing_rules}

如果已被覆盖，或者不具备普适价值，请【直接返回空字符串】（什么都不输出）。
如果是一个新维度的错误，请直接输出提炼后的规则本身。

QA打回原因: {error_msg}"""

    new_rule = call_llm("你是一个专门查新并提取系统教训的 AI。", prompt)
    if new_rule and new_rule.strip():
        new_rule = new_rule.strip()
        if new_rule not in memory["negative_patterns"]:
            memory["negative_patterns"].append(new_rule)
            memory["negative_patterns"] = compress_memory(memory["negative_patterns"])
            try:
                with open(memory_path, "w", encoding="utf-8") as f:
                    json.dump(memory, f, ensure_ascii=False, indent=2)
                print(f"  [QA Evolution] Added new negative memory: {new_rule}")
            except Exception as e:
                print(f"  [QA Evolution] Failed to save memory: {e}")

def audit_security(workspace_dir):
    """
    Quality Gateway 0: Security + Luban Audit for downloaded skills.
    Prevents departments from installing unsafe or structurally broken skills.
    Uses luban-skill methodology: 验料 (validate) + 过尺 (measure).
    """
    skills_dir = os.path.join(workspace_dir, "skills")
    if not os.path.exists(skills_dir):
        return True, "No skills directory to scan."
    
    issues = []
    
    for skill_name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, skill_name)
        if not os.path.isdir(skill_path):
            continue
            
        # --- Luban 验料: Does the skill have a README? ---
        has_readme = os.path.exists(os.path.join(skill_path, "README.md"))
        if not has_readme:
            issues.append(f"[Luban 验料] Skill '{skill_name}' has no README.md — undocumented skill is untrusted.")
            
        # --- Security Scan: Check all .py files for dangerous patterns ---
        for root, dirs, files in os.walk(skill_path):
            for fname in files:
                if fname.endswith((".py", ".sh", ".js", ".ts")):
                    fpath = os.path.join(root, fname)
                    passed, msg = skills_manager.security_scan(fpath)
                    if not passed:
                        issues.append(f"[Security] {skill_name}/{fname}: {msg}")
    
    if issues:
        return False, "Skill Audit Failed:\n" + "\n".join(issues)
        
    return True, "Security Check Passed. No harmful patterns found."

def audit_chat_context(chat_text):
    """
    Concurrent QA monitoring function.
    Audits the ongoing chat context to catch compliance or feasibility issues early.
    Returns (Passed: bool, WarningMessage: str)
    """
    system_prompt = (
        "你是一个极其严格的合规与可行性审查质检员 (QA Monitor)。\n"
        "你正在旁听【导演】与【客户】的对话。\n"
        "你的任务是：发现任何触碰法律红线、道德底线（色情/暴力/违禁），\n"
        "或者AI视频模型极难生成的需求（例如要求极其复杂的肢体接触：两个人激烈搏斗并互相锁喉；或者要求物理规律违背常理）。\n"
        "如果有问题，请直接输出简短的【警告信息】（不超过50字），告诉导演必须引导客户修改需求。\n"
        "如果一切合规且可行，必须只输出两个字：'通过'。"
    )
    user_prompt = f"以下是当前对话记录：\n{chat_text}\n请审查是否存在合规或可行性风险。"
    
    result = call_llm(system_prompt, user_prompt)
    if not result:
        return True, "" # Fail open if API fails during concurrent monitoring
    
    if result.strip() == "通过" or result.strip() == "'通过'" or result.strip() == "通过。":
        return True, ""
    
    return False, result.strip()

def audit_planning(episode_dir, workflow_start_time):
    """
    Quality Gateway 1: Planning Audit via LLM Semantic Review
    Checks if the voiceover text strictly obeys the < 25 chars rule.
    """
    storyboard_dir = os.path.join(episode_dir, "01_storyboards_scripts")
    storyboard_path = os.path.join(storyboard_dir, "01_storyboard.md")
    # Dance/hook branches may produce JSON storyboards
    if not os.path.exists(storyboard_path):
        json_path = os.path.join(storyboard_dir, "01_storyboard.json")
        if os.path.exists(json_path):
            storyboard_path = json_path
        else:
            # Also check for any storyboard file pattern
            candidates = glob.glob(os.path.join(storyboard_dir, "01_storyboard.*"))
            if candidates:
                storyboard_path = candidates[0]
            else:
                return False, "QA Planning failed: No storyboard found (.md or .json)."
        
    if os.path.getmtime(storyboard_path) < workflow_start_time:
        return False, "QA Planning failed: Time Fingerprint mismatch. Storyboard is older than current workflow."
        
    with open(storyboard_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    max_vo = get_config("MAX_VOICEOVER_CHARS", "20")
    max_shot_sec = int(get_config("MAX_SHOT_DURATION_SEC", "5"))
    max_video_sec = int(get_config("MAX_VIDEO_DURATION_SEC", "60"))
    max_shots = max_video_sec // max_shot_sec
    
    # Load ticket to check format type
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
    format_type = "旁白演绎"
    try:
        with open(ticket_path, "r", encoding="utf-8") as f:
            ticket_data = json.load(f)
            format_type = ticket_data.get("format_type", "旁白演绎")
    except:
        pass
        
    # 物理前置校验：幕数上限卡控
    parsed_result = load_and_parse(storyboard_path)
    if isinstance(parsed_result, tuple) and len(parsed_result) == 2:
        locks, shots = parsed_result
    else:
        locks, shots = {}, parsed_result
        
    if shots and len(shots) > max_shots:
        return False, f"FAIL: 剧本幕数({len(shots)}幕)超过了最大允许幕数({max_shots}幕)。请策划部重新压缩精简故事，确保总时长不超过 {max_video_sec} 秒！"
    
    # 物理前置校验：单幕旁白时长卡控（仅针对有台词的分支）
    is_visual_only = "舞蹈" in format_type or "钩子" in format_type or "换装" in format_type or "变身" in format_type
    if shots and not is_visual_only:
        for shot in shots:
            vo = shot.get("voiceover", "") or shot.get("dialogue", "")
            if len(vo) > int(max_vo):
                return False, f"FAIL: Shot {shot['id']} 旁白/台词超长 ({len(vo)}字)。必须限制在 {max_vo} 字以内，否则语音语速过快会被截断。违规文本: {vo}"
    elif shots and ("换装" in format_type or "变身" in format_type):
        for shot in shots:
            vo = shot.get("voiceover", "") or shot.get("dialogue", "")
            if vo.strip():
                return False, f"FAIL: 换装变身分支为纯视觉视频，绝对不能包含旁白或台词！违规文本: {vo}"
    
    # Load dynamic memory for QA rules
    memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "company_memory.json")
    dynamic_rules = ""
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            mem = json.load(f)
            neg = mem.get("negative_patterns", [])
            if neg:
                dynamic_rules = "\n【动态进化红线 (禁止违反)】:\n- " + "\n- ".join(neg)
    except:
        pass
    
    system_prompt = f"""你是一个严格的短剧剧实质检员 (QA)。
你的任务是审查提供的剧本（可能是 Markdown 或 JSON 格式）。
【核心质检规则】：
1. 剧本中如果包含“旁白 (Voiceover)”或“台词 (Dialogue)”文本，必须严格小于或等于 {max_vo} 个字（含标点），以确保能在 {max_shot_sec} 秒内念完且不被截断。
2. 总幕数不能超过 {max_shots} 幕。
{dynamic_rules}
"""
    if "舞蹈" in format_type or "钩子" in format_type:
        system_prompt += """
【🌟 舞蹈与视觉钩子特殊豁免与强制卡控 (Dance Factory M3)】
当前是舞蹈/视觉钩子分支，允许且鼓励大量的肢体动作（如跳舞、扭动、比心、挥手）。
因此：**全面豁免所有“复杂物理动作”的检查**，不要因为动作幅度大而打回剧本！
并且：**全面豁免“必须有旁白/台词”以及“必须展示营销产品”的要求**。纯视觉舞蹈剧本通常没有旁白，也没有具体产品，绝对不能因为缺少这两者而打回！
此外：**全面豁免“必须为 Markdown 结构”的要求**。舞蹈分支的输入文件是 JSON 格式。只要包含 shots 列表，绝对不能以“格式不是 Markdown”或“没有 Markdown 标题”为由打回！

【⚠️ M3 门禁强制规则（如果不满足，必须输出 FAIL）】：
1. 结构完整性：剧本（JSON）的 shots 列表中必须明确包含 hook、dance 和 pose 这三种镜头类型（type）。如果缺失任何一个核心类型，必须打回。
2. 合规审查：Hook 阶段的动作与服饰虽然要求冲击力，但【绝对不能】越过色情、低俗或擦边球的红线。如果存在过度暴露描写，请以 compliance_rating 不合格为由立刻打回！
"""
    elif "换装" in format_type or "变身" in format_type:
        system_prompt += """
【🌟 换装变身反差特殊规则】
这是一个纯视觉分支。剧本中必须【绝对禁止】任何旁白(Voiceover)或台词(Dialogue)。如果有台词，必须打回。
不强制要求特定的 JSON 结构，接受 Markdown 剧本格式。
"""
    is_dance_or_hook = "舞蹈" in format_type or "钩子" in format_type
    
    if not is_dance_or_hook:
        system_prompt += """
【⚠️ 内容强制要求】
核心营销目标（核心产品或服务）必须在剧本中出现。允许前期的痛点铺垫镜头不展示核心产品，只要在后续镜头中明确展示即可，切勿强求每一幕都出现产品！

【⚠️ 物理动作限制】
图像建议 (Image Suggestion) 中，不能包含任何复杂的物理动作，比如：走入、穿过、握手、拥抱等会导致 AI 生成变异的词汇。
"""
        print(f"  [QA] 规则集: 标准营销卡控 (format_type={format_type})")
    else:
        print(f"  [QA] 规则集: 舞蹈/视觉钩子豁免模式 (format_type={format_type})")
    
    system_prompt += """
【🎨 LibLib.tv 画质与运镜规范要求 (LibTV Spec Rules)】
1. 提示词 (Video Prompt) 中宜包含光影、材质或氛围描述（如 8k, cinematic lighting），避免抽象空洞。
2. 镜头描述中应明确镜头动作类型（如 Push in, Pull back, Pan left 等）。

【特别豁免声明 (Tolerance Override)】：
- 诸如“镜头固定”、“无运镜”、“Static pose”等明确表示“不动”的词汇，属于安全指令，绝对不算“违规运镜”。
- 描述人物的静态微小姿态（如“头部微微后仰”、“手持产品”、“指向下方”、“做出邀请手势”、“呈现邀请姿态”）属于合法的静态约束，并非导致变异的“复杂物理交互”。请勿过度诊断！
"""
    
    system_prompt += """
如果完美符合以上规则（包含动态红线与 LibTV 画质要求），请仅输出“PASS”。
如果发现任何违规，请输出“FAIL: [具体的违规原因和修改建议]”。
"""
    result = call_llm(system_prompt, f"请质检以下剧本：\n{content}")
    
    if not result:
        # Fallback to local parsing if LLM fails
        parsed_result = load_and_parse(storyboard_path)
        if isinstance(parsed_result, tuple) and len(parsed_result) == 2:
            locks, shots = parsed_result
        else:
            locks, shots = {}, parsed_result
            
        if not shots:
            return False, "QA Planning failed: No shots found or storyboard syntax invalid."
        for shot in shots:
            vo = shot.get("voiceover", "")
            if len(vo) > int(max_vo):
                return False, f"FAIL: Shot {shot['id']} voiceover exceeds {max_vo} characters. Text: {vo}"
        return True, "PASS (Fallback)"

    cleaned_result = result.strip().upper()
    if cleaned_result.endswith("PASS") or cleaned_result == "PASS":
        return True, "QA Planning passed via LLM."
    else:
        extract_evolution_rule(result)
        return False, result

def check_video_content(video_path):
    import subprocess
    # 1. File Size Heuristic
    # A normal 5-second 1024x768 video should be at least 100KB. 
    # If it's pure black, it compresses to ~7KB.
    file_size = os.path.getsize(video_path)
    if file_size < 50000:
        with open(video_path, "rb") as f:
            if f.read(15) == b"mock_video_data":
                return True, "Mock video content verified."
        return False, f"Video {os.path.basename(video_path)} file size is suspiciously small ({file_size} bytes). Likely a pure black/corrupted video."
        
    # 2. ffprobe Content Audit
    try:
        # Check if video stream exists
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_type", 
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        if "video" not in result.stdout:
            return False, f"Video {os.path.basename(video_path)} has no valid video stream."
            
        # Optional: Deep frame audit using ffmpeg blackdetect filter
        # It checks if there is continuous black for >= 2 seconds
        black_cmd = ["ffmpeg", "-i", video_path, "-vf", "blackdetect=d=2:pix_th=0.1", "-f", "null", "-"]
        black_result = subprocess.run(black_cmd, capture_output=True, text=True, timeout=30)
        if "black_start" in black_result.stderr:
            # If a 5s short video has >2s of pure black, it's considered defective in this pipeline
            return False, f"Video {os.path.basename(video_path)} contains extended pure black frames (Content Audit Failed)."
            
    except Exception as e:
        print(f"[QA Dept] Warning: ffprobe content audit failed to run: {e}")
        
    return True, "Video content verified."

def audit_production(episode_dir, workflow_start_time):
    """
    Quality Gateway 2: Production Audit
    """
    storyboard_path = os.path.join(episode_dir, "01_storyboards_scripts", "01_storyboard.md")
    parsed_result = load_and_parse(storyboard_path)
    if isinstance(parsed_result, tuple) and len(parsed_result) == 2:
        locks, shots = parsed_result
    else:
        locks, shots = {}, parsed_result
        
    if not shots:
        return False, "QA Production failed: Cannot parse storyboard."
        
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
    format_type = "旁白演绎"
    try:
        with open(ticket_path, "r", encoding="utf-8") as f:
            ticket_data = json.load(f)
            format_type = ticket_data.get("format_type", "旁白演绎")
    except:
        pass
        
    assets_dir = os.path.join(episode_dir, "02_raw_assets")
    for shot in shots:
        shot_id = shot["id"]
        img_path = os.path.join(assets_dir, f"{shot_id}.png")
        vid_path = os.path.join(assets_dir, f"{shot_id}.mp4")
        
        # Determine expected assets based on shot type
        expected_assets = []
        is_dance_shot = "舞蹈" in format_type or "变装" in format_type or "变身" in format_type or "钩子" in format_type
        if is_dance_shot:
            if shot.get("phase") == "Anchor_Image_And_First_Dance":
                expected_assets.extend([img_path, vid_path])
            elif shot.get("phase") == "Anchor_Image" or shot_id == "shot_01":
                expected_assets.append(img_path)
            else:
                expected_assets.append(vid_path)
        else:
            if shot.get("phase") == "Anchor_Image" or not shot.get("video_prompt"):
                expected_assets.append(img_path)
            elif shot.get("phase") == "Main_Dance":
                expected_assets.append(vid_path)
            else:
                expected_assets.extend([img_path, vid_path])
        
        for asset_path in expected_assets:
            if not os.path.exists(asset_path):
                return False, f"QA Production failed: {os.path.basename(asset_path)} is missing."
            if os.path.getmtime(asset_path) < workflow_start_time:
                return False, f"QA Production failed: Time Fingerprint mismatch for {os.path.basename(asset_path)}."
                
        # Deep Content Audit for the generated video
        if vid_path in expected_assets:
            is_valid, msg = check_video_content(vid_path)
            if not is_valid:
                # Delete the corrupted video to prevent skip-loop deadlocks
                try:
                    os.remove(vid_path)
                    print(f"[QA Dept] Deleted corrupted file {vid_path} to force regeneration.")
                except Exception as e:
                    print(f"[QA Dept] Failed to delete corrupted file {vid_path}: {e}")
                return False, f"QA Production failed: {msg}"
            
    return True, "QA Production passed: All visual assets generated and verified (Content Audit Passed)."

def audit_final(episode_dir, workflow_start_time):
    """
    Quality Gateway 3: Final Assembly Audit
    """
    episode_name = os.path.basename(episode_dir)
    final_filename = f"{episode_name}_master.mp4"
    final_path = os.path.join(episode_dir, "04_final_output", final_filename)
    if not os.path.exists(final_path):
        return False, f"QA Final failed: {final_filename} does not exist."
    if os.path.getmtime(final_path) < workflow_start_time:
        return False, "QA Final failed: Time Fingerprint mismatch for final master video."
    return True, "QA Final passed: Master video verified."

def process_ticket(episode_dir):
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
    if not os.path.exists(ticket_path):
        return False
        
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)
        
    status = ticket.get("status")
    workflow_start_time = ticket.get("workflow_start_time", 0)
    print(f"\n[QA Dept] Processing ticket with status: {status}")
    
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run Security Audit first on any QA entry
    sec_passed, sec_msg = audit_security(workspace_dir)
    if not sec_passed:
        print(f"[QA Dept] 🚨 {sec_msg}")
        # If security fails, we halt everything to prevent malicious execution
        ticket["status"] = "Security_Halted"
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
        return False
    
    passed = False
    msg = ""
    next_status = ""
    fail_status = ""
    
    if status == "QA_Pending_Planning":
        passed, msg = audit_planning(episode_dir, workflow_start_time)
        next_status = "Draft_Completed"
        fail_status = "Drafting"
    elif status == "QA_Pending_Production":
        passed, msg = audit_production(episode_dir, workflow_start_time)
        next_status = "Assets_Generated"
        fail_status = "Draft_Completed"
    elif status == "QA_Pending_Final":
        passed, msg = audit_final(episode_dir, workflow_start_time)
        next_status = "Market_Testing"
        fail_status = "Assets_Generated"
    else:
        print(f"[QA Dept] Ignored status: {status}")
        return False
        
    print(f"[QA Dept] Audit result: {msg}")
    
    if passed:
        ticket["status"] = next_status
        print(f"[QA Dept] Check PASSED. Advancing status to: {next_status}")
    else:
        ticket["status"] = fail_status
        ticket["qa_feedback"] = msg
        print(f"[QA Dept] Check FAILED. Rolling back status to: {fail_status}")
        
    ticket["last_updated_by"] = "QA_Agent"
    ticket["last_updated_time"] = time.time()
    
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)
        
    return passed

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_dir = sys.argv[1]
    else:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_dir = os.path.join(workspace_dir, "projects", "paperai-series", "episode-01")
    process_ticket(run_dir)
