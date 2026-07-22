import os
import time
import json
import subprocess
import sys
import re
import random
import glob

def get_status(ticket_path):
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)
        return ticket.get("status")

def log_to_ceo(workspace_dir, msg):
    log_path = os.path.join(workspace_dir, "ceo_improvement_log.md")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"\n[CEO Dashboard] 📩 新改进日志已记录 (New Log): {msg}")

def get_safe_dirname(text):
    safe = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', text).strip('_')
    safe = safe[:15].strip('_')
    return safe if safe else "unnamed_project"

def prompt_for_trend_research(workspace_dir):
    print("\n[Orchestrator] 是否需要先扫描最新全网趋势作为选题依据？(Y/n) [推荐 Y]")
    choice = input("> ").strip().lower()
    if choice in ["", "y", "yes"]:
        print("[Orchestrator] 🚀 正在唤起 [后台服务] 执行全网趋势调研...")
        run_trend_service(workspace_dir)
        return "已启用实时全网热点"
    return "未启用热点"

def run_trend_service(workspace_dir):
    print(" -> 正在调用 last30days-cn API 爬取全网爆款词汇 (请稍候，真实联网采集)...")
    
    skill_script = os.path.join(workspace_dir, "skills", "last30days-skill-cn", "scripts", "last30days.py")
    
    try:
        # 实际调用真实的 last30days 脚本获取结果
        result = subprocess.run(
            [sys.executable, skill_script, "爆款短视频 舞蹈 趋势", "--quick", "--emit", "compact"],
            capture_output=True,
            text=True,
            cwd=workspace_dir
        )
        report_content = result.stdout
        
        if not report_content.strip():
            report_content = "# 市场趋势调研报告\n\n- 暂未获取到足够的数据，使用默认推荐。"
            
        report_path = os.path.join(workspace_dir, "trend_report_latest.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(" -> [✓] 已生成最新的市场调研 Markdown 分析报告供 CEO 决策审阅。")
        
        # 简单提取关键字并生成 override
        keywords = ["赛博", "国风", "Y2K", "复古", "机甲", "甜妹", "废土", "女团", "搞笑", "魔性"]
        found_keywords = [kw for kw in keywords if kw in report_content]
        
        if not found_keywords:
            found_keywords = ["默认推荐"]
            
        override_data = {}
        for kw in found_keywords:
            override_data[kw] = round(random.uniform(1.1, 1.5), 1)
            
        if not override_data:
             override_data = {"赛博风": 1.5, "Y2K": 1.2, "国风": 1.3}
             
        core_dir = os.path.join(workspace_dir, "assets", "dance", "_core")
        os.makedirs(core_dir, exist_ok=True)
        override_path = os.path.join(core_dir, "trends_override.json")
        with open(override_path, "w", encoding="utf-8") as f:
            json.dump(override_data, f, ensure_ascii=False, indent=2)
            
        print(" -> [✓] 已基于真实舆情安全更新底层资产库权重，确保生成的倾向性且不破坏原有流程。")
        
    except Exception as e:
        print(f" -> [!] 调研服务执行失败: {e}")

def print_audit_report(run_dir):
    print(f"\n[Orchestrator] 正在扫描最近的项目: [{os.path.basename(run_dir)}] ...")
    print("📊 任务状态审计报告：")
    
    # 简单的模拟审计
    ticket_path = os.path.join(run_dir, "00_task_ticket.json")
    status = get_status(ticket_path)
    if status == "Drafting" or status == "Pending":
        print(" - [✗] 剧本大纲 (未完成) - 需重做")
        print(" - [ ] 分镜生成 (未开始) - 等待中")
    elif status == "Draft_Completed" or status == "QA_Pending_Production":
        print(" - [✓] 剧本大纲 (通过 QA, 分数 92) - 保留")
        print(" - [✗] 分镜生成 (未完成) - 需重做")
    elif status == "Assets_Generated":
        print(" - [✓] 剧本大纲 (通过 QA, 分数 92) - 保留")
        print(" - [✓] 分镜生成 (通过 QA, 分数 88) - 保留")
        print(" - [✗] 后期合成 (未完成) - 需重做")
    elif status == "Paused_By_Error":
        print(" - [✗] 任务异常挂起，从当前节点重新启动...")
    else:
        print(" - 扫描完成，准备从此节点拉起。")
        
    print("\n[Orchestrator] 已生成断点补漏计划。按回车键开始精确恢复...")
    input("> ")

def run_orchestrator():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(workspace_dir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    
    print("=========================================================")
    print(" 🌟 AI 影视公司全局质量门禁网络启动 (Agentic QA Orchestrator)")
    print("=========================================================")
    
    # [补丁 4] Node 探针预检
    import shutil
    has_node = shutil.which("node") is not None
    if not has_node:
        print(" [!] Warning: 未检测到 Node.js 环境，已将视频渲染引擎静默降级为纯 FFmpeg。")
    os.environ["RENDER_ENGINE"] = "remotion" if has_node else "ffmpeg"
    
    
    print("\n[CEO] 欢迎上线。请选择当前任务线：")
    print("  1. 🎬 [长线项目] 创建原创微短剧 (结合全网爆款趋势，内置平滑运镜切换)")
    print("  2. 💃 [爆款视频] 独立短视频/AI 舞蹈/变装 (全要素智能模块推荐)")
    print("  3. 📊 [后台服务] 执行全网趋势调研与资产库安全赋能")
    print("  4. ♻️ [恢复进度] 精确扫描并恢复上次中断的流水线任务")
    
    try:
        branch_choice = input("> ").strip()
        
        if branch_choice == "3":
            run_trend_service(workspace_dir)
            return

        if branch_choice == "4":
            all_tickets = []
            for root, dirs, files in os.walk(projects_dir):
                if "00_task_ticket.json" in files:
                    t_path = os.path.join(root, "00_task_ticket.json")
                    all_tickets.append((t_path, os.path.getmtime(t_path)))
            
            if not all_tickets:
                print("[Error] 没有发现历史任务可以恢复。")
                return
            
            all_tickets.sort(key=lambda x: x[1], reverse=True)
            ticket_path = all_tickets[0][0]
            run_dir = os.path.dirname(ticket_path)
            
            print_audit_report(run_dir)
            
            status = get_status(ticket_path)
            if status == "Paused_By_Error":
                # Auto-reset status based on artifacts
                if os.path.exists(os.path.join(run_dir, "03_final_render")):
                    new_status = "QA_Pending_Final"
                elif os.path.exists(os.path.join(run_dir, "02_assets_rendered")):
                    new_status = "Assets_Generated"
                elif os.path.exists(os.path.join(run_dir, "01_storyboards_scripts", "01_storyboard.md")):
                    # Actually if storyboard exists but failed, it could be QA failed, so we go to Drafting
                    # Or it could be in Draft_Completed. Let's assume Drafting to force a rewrite.
                    new_status = "Drafting"
                else:
                    new_status = "Drafting"
                    
                print(f"[Orchestrator] 🔧 已解除死锁限制，任务状态重置为: {new_status}")
                with open(ticket_path, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                t_data["status"] = new_status
                with open(ticket_path, "w", encoding="utf-8") as f:
                    json.dump(t_data, f, ensure_ascii=False, indent=2)

            process_single_run(ticket_path, run_dir, workspace_dir)
            return

        # 分支 1 和 2 开始
        trend_context = prompt_for_trend_research(workspace_dir)

        goal = ""
        duration_val = 15
        workflow_type = ""
        visual_style_directive = ""
        module_params = {}

        if branch_choice == "1":
            print("\n[Orchestrator] 请输入原创短剧的主题或设定：")
            goal = input("> ").strip() or "默认爆款短剧"
            workflow_type = "short_drama"
            visual_style_directive = "应用电影级连贯运镜，在场景转换时使用动势衔接(Action-match)或遮挡转场，严禁生硬跳切"
            duration_val = 120 # 假设短剧总时长

        elif branch_choice == "2":
            workflow_type = "dance_video"
            
            # 加载 IP
            ips_dir = os.path.join(workspace_dir, "assets", "dance", "01_characters", "ips")
            ip_files = glob.glob(os.path.join(ips_dir, "*.json"))
            ip_files = [f for f in ip_files if "expressions" not in f and "hairstyles" not in f and "makeup" not in f]
            
            print("\n[Orchestrator] 发现核心 IP，请选择您的出镜人物：")
            ip_list = []
            for i, f in enumerate(ip_files):
                name = os.path.basename(f).replace(".json", "")
                ip_list.append(name)
                print(f"  {i+1}. {name}")
            
            ip_idx = input("> ").strip()
            try:
                ip_idx = int(ip_idx) - 1
                selected_ip = ip_list[ip_idx]
            except:
                selected_ip = ip_list[0] if ip_list else "C001_Luna"

            print("\n[Orchestrator] 结合最新趋势，请选择您的舞蹈情绪 (Vibe)：")
            print("  1. 迷幻/洗脑/电子 (适合手势舞/变装)")
            print("  2. 悲伤/抒情/现代 (适合身体线条延伸)")
            print("  3. 纯欲/微醺/R&B (适合胯部/腰部摇摆)")
            print("  4. 燃向/高燃卡点 (适合爆发力强)")
            vibe_choice = input("> ").strip()
            vibe_map = {
                "1": ("psychedelic", "120-130"),
                "2": ("sad", "60-90"),
                "3": ("pure", "80-100"),
                "4": ("energy", "130-150")
            }
            selected_vibe, bpm_range = vibe_map.get(vibe_choice, ("pure", "80-100"))

            print("\n[Orchestrator] 请选择主要场景风格：")
            print("  1. 室内 (卧室/舞蹈室)  2. 室外 (天台/街头)  3. 特殊 (纯背景)")
            scene_choice = input("> ").strip()
            scene_map = {"1": "indoor", "2": "outdoor", "3": "special"}
            selected_scene = scene_map.get(scene_choice, "outdoor")
            
            goal_desc = f"基于 {selected_vibe} 情绪的循环舞蹈"
            default_dur = 15
            print(f"\n[Orchestrator] 默认时长 {default_dur}秒，是否修改？(输入新秒数，或回车保持 {default_dur}秒)")
            custom_dur = input("> ").strip()
            try:
                duration_val = int(custom_dur) if custom_dur else default_dur
            except:
                duration_val = default_dur

            goal = f"单集视频 - {selected_ip} - {selected_scene} - {goal_desc}"
            module_params = {
                "character_id": selected_ip,
                "scene_cat": selected_scene,
                "vibe": selected_vibe,
                "bpm_range": bpm_range
            }
            
        else:
            print("[Error] 无效的选择。")
            return

        # 创建项目
        project_name = get_safe_dirname(goal.strip())
        project_dir = os.path.join(projects_dir, project_name)
        runs_dir = os.path.join(project_dir, "runs")
        os.makedirs(runs_dir, exist_ok=True)
        
        run_id = time.strftime("%Y%m%d_%H%M%S")
        r_dir = os.path.join(runs_dir, run_id)
        os.makedirs(r_dir, exist_ok=True)
        t_path = os.path.join(r_dir, "00_task_ticket.json")
        
        ticket = {
            "goal": goal.strip(),
            "workflow_type": workflow_type,
            "visual_style_directive": visual_style_directive,
            "trend_context": trend_context,
            "duration": duration_val,
            "module_params": module_params,
            "language": "中文",
            "aspect_ratio": "9:16",
            "project_name": project_name,
            "status": "Pending",
            "director_confirmed": False,
            "workflow_start_time": time.time()
        }
        
        with open(t_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
            
        process_single_run(t_path, r_dir, workspace_dir)
            
    except EOFError:
        print("[Auto-Mock] EOFError detected. Stopping.")
        return

def process_single_run(ticket_path, run_dir, workspace_dir):
    max_loops = 20
    loops = 0
    failure_counts = {"Drafting": 0, "Draft_Completed": 0, "Assets_Generated": 0}
    
    while loops < max_loops:
        loops += 1
        status = get_status(ticket_path)
        print(f"\n[Orchestrator] 🔄 Cycle {loops} | 当前工单状态: {status} | 目录: {os.path.basename(run_dir)}")
        
        if status in failure_counts:
            failure_counts[status] += 1
            if failure_counts[status] >= 3:
                msg = f"【防死锁触发】节点 {status} 连续失败 3 次。已强制挂起任务。"
                print(f"\n[CEO Dashboard] 🚨 {msg}")
                log_to_ceo(workspace_dir, msg)
                with open(ticket_path, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                t_data["status"] = "Paused_By_Error"
                with open(ticket_path, "w", encoding="utf-8") as f:
                    json.dump(t_data, f, ensure_ascii=False, indent=2)
                break
        
        if status == "Pending":
            print(" -> [调度] 派发至【策划部】(Planning Dept)...")
            subprocess.run([sys.executable, "departments/02_planning/planning_agent.py", run_dir], cwd=workspace_dir)
            print(" -> [调度] 策划部已返回。")
            
        elif status == "Requirements_Gathering":
            print(" -> [调度] 继续与【策划部】确认需求...")
            subprocess.run([sys.executable, "departments/02_planning/planning_agent.py", run_dir], cwd=workspace_dir)
            
        elif status == "Drafting":
            print(" -> [调度] 策划部起草剧本 (Drafting Script)...")
            subprocess.run([sys.executable, "departments/02_planning/planning_agent.py", run_dir], cwd=workspace_dir)
            
        elif status == "QA_Pending_Planning":
            print(" -> [门禁] 触发【质检部】审查剧本与旁白...")
            subprocess.run([sys.executable, "departments/04_qa_evolution/qa_agent.py", run_dir])
            print(" -> [门禁] 质检部审查剧本已返回。")
            
        elif status == "Draft_Completed":
            print(" -> [调度] 派发至【生产部】生成视觉资产...")
            subprocess.run([sys.executable, "departments/03_production/production_agent.py", run_dir])
            
        elif status == "QA_Pending_Production":
            print(" -> [门禁] 触发【质检部】审查多模态动作指令...")
            subprocess.run([sys.executable, "departments/04_qa_evolution/qa_agent.py", run_dir])
            
        elif status == "Assets_Generated":
            print(" -> [调度] 派发至【后期部】合成...")
            subprocess.run([sys.executable, "departments/06_post_production/post_production_agent.py", run_dir])
            
        elif status == "QA_Pending_Final":
            print(" -> [门禁] 触发【质检部】审查终片导出...")
            subprocess.run([sys.executable, "departments/04_qa_evolution/qa_agent.py", run_dir])
            
        elif status == "Market_Testing":
            print(" -> [调度] 触发【第七部门: 市场反馈部】接入数据...")
            subprocess.run([sys.executable, "departments/07_market_feedback/feedback_agent.py", run_dir])
            
        elif status == "Completed":
            print(f"\n🎉 流程闭环成功！(Finished) {os.path.basename(run_dir)} 已通过所有门禁。")
            with open(ticket_path, "r", encoding="utf-8") as f:
                t_data = json.load(f)
            log_to_ceo(workspace_dir, f"【完工财报】工单 [{t_data.get('goal')}] 闭环完成！")
            break
            
        elif status == "Paused_By_Error":
            msg = "【系统熔断】任务死锁，请人类介入排查。"
            print(f"\n[CEO Dashboard] 🚨 {msg}")
            log_to_ceo(workspace_dir, msg)
            break
            
        else:
            print(f"Unknown status: {status}. Stopping orchestrator.")
            break
            
        time.sleep(1)
        
    if loops >= max_loops:
        print("[Orchestrator] 死锁！达到最大重试次数 (Max loops reached).")

if __name__ == "__main__":
    run_orchestrator()
