import os
import time
import json
import subprocess
import sys
import re
import random
try:
    import readline
except ImportError:
    pass

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
    # Limit to 15 characters to avoid excessively long folder names
    safe = safe[:15].strip('_')
    return safe if safe else "unnamed_project"

def run_orchestrator():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(workspace_dir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    
    print("=========================================================")
    print(" 🌟 AI 影视公司全局质量门禁网络启动 (Agentic QA Orchestrator)")
    print("=========================================================")
    
    print("\n[CEO] 请选择创建分支 (输入 1-3) [直接回车以恢复最新历史任务]:")
    print("  1. 旁白演绎 (适合信息密度高的干货/盘点类)")
    print("  2. 真人剧场情景 (适合有冲突、有反转的剧情向)")
    print("  3. AI舞蹈与视觉钩子 (适合强视觉冲击、情绪向、洗脑类)")
    
    try:
        branch_choice = input("> ").strip()
        if branch_choice:
            branch_map = {
                "1": "旁白演绎",
                "2": "真人剧场情景",
                "3": "AI舞蹈与视觉钩子"
            }
            selected_branch = branch_map.get(branch_choice, "AI舞蹈与视觉钩子")
            
            if branch_choice == "3":
                print(f"\n[CEO] 您已选择【{selected_branch}】。请输入本次的视觉主题或人物设定 (例如：赛博朋克风女团舞，吸引年轻粉丝)：")
            else:
                print(f"\n[CEO] 您已选择【{selected_branch}】。请输入本次的营销目标或主题 (例如：推销最新款丝绒口红)：")
            
            goal = input("> ").strip()
            if not goal:
                goal = "默认目标"

            if branch_choice == "3":
                print("\n[CEO] 请输入舞蹈时长 (如: 15秒, 30秒) [默认: 15秒]:")
                duration = input("> ").strip() or "15秒"
                print("\n[CEO] 请输入舞蹈风格 (如: 赛博朋克, 韩舞, 古风) [默认: 韩舞]:")
                dance_style = input("> ").strip() or "韩舞"
                print("\n[CEO] 请输入具体动作要求 (如: 科目三, 扭腰) [默认: 无]:")
                motion_req = input("> ").strip() or "无"
                
                goal = f"{goal}，时长：{duration}，风格：{dance_style}，动作要求：{motion_req}"
                language = "中文"
                aspect_ratio = "9:16"
                voice_style = "无"
            else:
                print("\n[CEO] 请输入全局语言 (如: 中文, English) [默认: 中文]:")
                language = input("> ").strip() or "中文"
                print("\n[CEO] 请选择视频长宽比 (如: 9:16, 16:9) [默认: 9:16]:")
                aspect_ratio = input("> ").strip() or "9:16"
                print("\n[CEO] 请选择旁白音色风格 (参考: 温柔女声, 磁性男声, 激情解说, 活力童声) [默认: 温柔女声]:")
                voice_style = input("> ").strip() or "温柔女声"

            # Create a new dynamic project
            project_name = get_safe_dirname(goal.strip())
            project_dir = os.path.join(projects_dir, project_name)
            runs_dir = os.path.join(project_dir, "runs")
            os.makedirs(runs_dir, exist_ok=True)
            
            run_id = time.strftime("%Y%m%d_%H%M%S")
            is_batch_mode = os.environ.get('BATCH_MODE', 'false').lower() == 'true'
            variants = ["A", "B", "C"] if is_batch_mode else [""]
            
            # Select a random routine to lock for the batch A/B test
            locked_routine_id = f"R0{random.randint(1, 8)}" if is_batch_mode else None
            
            created_runs = []
            for suffix in variants:
                r_id = f"{run_id}_{suffix}" if suffix else run_id
                r_dir = os.path.join(runs_dir, r_id)
                os.makedirs(r_dir, exist_ok=True)
                t_path = os.path.join(r_dir, "00_task_ticket.json")
                import re
                duration_digits = re.search(r'\d+', locals().get("duration", "15"))
                duration_val = int(duration_digits.group()) if duration_digits else 15
                ticket = {
                    "goal": goal.strip(),
                    "language": language,
                    "aspect_ratio": aspect_ratio,
                    "voice_style": voice_style,
                    "selected_branch": selected_branch,
                    "project_name": project_name,
                    "status": "Pending",
                    "director_confirmed": False,
                    "workflow_start_time": time.time(),
                    "batch_variant": suffix,
                    "locked_routine_id": locked_routine_id,
                    "duration": duration_val
                }
                with open(t_path, "w", encoding="utf-8") as f:
                    json.dump(ticket, f, ensure_ascii=False, indent=2)
                created_runs.append((t_path, r_dir))
                
            for t_path, r_dir in created_runs:
                process_single_run(t_path, r_dir, workspace_dir)
                
        else:
            # Resume latest run across all projects (find most recently modified ticket)
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
            with open(ticket_path, "r", encoding="utf-8") as f:
                ticket = json.load(f)
            print(f"[Orchestrator] 恢复最新历史任务: {run_dir}")
            process_single_run(ticket_path, run_dir, workspace_dir)
            
    except EOFError:
        print("[Auto-Mock] EOFError detected. Creating a new run with default goal.")
        project_name = "推销_PaperAI_最新功能"
        project_dir = os.path.join(projects_dir, project_name)
        runs_dir = os.path.join(project_dir, "runs")
        run_id = time.strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(runs_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)
        ticket_path = os.path.join(run_dir, "00_task_ticket.json")
        ticket = {
            "goal": "推销 PaperAI 最新功能",
            "project_name": project_name,
            "status": "Pending",
            "director_confirmed": False,
            "workflow_start_time": time.time()
        }
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)
            
        process_single_run(ticket_path, run_dir, workspace_dir)

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
