import asyncio
import os
import sys
import time
import json
import contextlib
from sqlmodel import Session, select
from models.database import engine, Project
from ws.logger import manager
if os.path.exists("/workspace/projects") or os.path.exists("/workspace"):
    BASE_DIR = "/workspace"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WSRedirector:
    def __init__(self, original_stdout, loop):
        self.original_stdout = original_stdout
        self.loop = loop

    def write(self, message):
        self.original_stdout.write(message)
        # Avoid sending just pure empty strings if possible, but keep newlines for formatting
        if message:
            asyncio.run_coroutine_threadsafe(manager.broadcast(message), self.loop)

    def flush(self):
        self.original_stdout.flush()

async def run_project_pipeline(project_id: int):
    # This runs in a background thread to avoid blocking the async event loop
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            return
            
        project.status = "Running"
        session.commit()
        
        launch_msg = f"[Pipeline] 🚀 Launching execution pipeline for project #{project.id} ({project.project_slug}). Format: {project.format_type}, Branch: {project.branch_type}"
        print(launch_msg)
        manager.broadcast_sync(launch_msg)
        
        # Prepare the file system structure expected by orchestrator
        projects_dir = os.path.join(BASE_DIR, "projects")
        project_dir = os.path.join(projects_dir, project.project_slug)
        runs_dir = os.path.join(project_dir, "runs")
        os.makedirs(runs_dir, exist_ok=True)
        
        run_id = time.strftime("%Y%m%d_%H%M%S")
        r_dir = os.path.join(runs_dir, run_id)
        os.makedirs(r_dir, exist_ok=True)
        t_path = os.path.join(r_dir, "00_task_ticket.json")
        
        # We need to bridge SQLite goal/format_type into the ticket format
        selected_branch = project.branch_type
        if project.branch_type == "handdraw_video":
            selected_branch = "手绘口播与剧情推演"
        elif project.branch_type == "dance_video":
            selected_branch = "AI舞蹈与视觉钩子"
        elif project.branch_type == "short_drama":
            selected_branch = "旁白演绎"

        ticket = {
            "goal": project.goal,
            "workflow_type": project.branch_type,
            "selected_branch": selected_branch,
            "selected_ip": project.selected_ip,
            "vibe": project.vibe,

            "trend_context": "已启用实时全网热点" if project.trend_enabled else "未启用热点",
            "visual_style_directive": "应用电影级连贯运镜，在场景转换时使用动势衔接(Action-match)或遮挡转场，严禁生硬跳切",
            "duration": 15,
            "module_params": {},
            "language": "中文",
            "aspect_ratio": "9:16" if project.format_type == "vertical" else "16:9",
            "project_name": project.project_slug,
            "status": "Pending",
            "director_confirmed": False,
            "workflow_start_time": time.time(),
            "sqlite_project_id": project.id # Store DB ID to sync back later
        }
        
        with open(t_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)

    # Run the blocking orchestrator via subprocess to capture all child logs
    try:
        loop = asyncio.get_running_loop()
        redirector = WSRedirector(sys.stdout, loop)
        
        env = os.environ.copy()
        env["CURRENT_WEB_PROJECT_ID"] = str(project_id)
        
        cmd = [
            sys.executable, "-u", "-c",
            f"import sys; sys.path.append('{BASE_DIR}'); from orchestrator import process_single_run; process_single_run('{t_path}', '{r_dir}', '{BASE_DIR}')"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            redirector.write(line.decode('utf-8', errors='replace'))
            
        await process.wait()
    except Exception as e:
        err_msg = f"[Pipeline] ❌ Subprocess error for project {project_id}: {e}"
        print(err_msg)
        manager.broadcast_sync(err_msg)
        
    # Sync final status back to SQLite
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if project:
            if os.path.exists(t_path):
                with open(t_path, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                    final_status = t_data.get("status", "Unknown")
                    if final_status == "Completed":
                        project.status = "Completed"
                    elif final_status == "Paused_By_Error":
                        project.status = "Paused_By_Error"
                    else:
                        project.status = final_status
            else:
                final_status = "Failed"
                project.status = final_status
            session.commit()
            
            end_msg = f"[Pipeline] 🏁 Project #{project_id} ({project.project_slug}) finished with status: {final_status}"
            print(end_msg)
            manager.broadcast_sync(end_msg)

async def worker_loop():
    start_msg = "[Worker] ⚙️ SQLite task worker online. Polling task queue..."
    print(start_msg)
    manager.broadcast_sync(start_msg)
    
    # 1. Crash recovery: On startup, recover tasks that were left 'Running'
    with Session(engine) as session:
        zombie_projects = session.exec(select(Project).where(Project.status == "Running")).all()
        for zp in zombie_projects:
            z_msg = f"[Worker] ⚠️ Recovered zombie running project: {zp.project_slug} -> reset to Pending"
            print(z_msg)
            manager.broadcast_sync(z_msg)
            zp.status = "Pending"
            session.add(zp)
        session.commit()
    
    # 2. Main polling loop
    ticks = 0
    while True:
        ticks += 1
        with Session(engine) as session:
            # Find one pending project
            pending_project = session.exec(select(Project).where(Project.status == "Pending").limit(1)).first()
            if pending_project:
                pickup_msg = f"[Worker] 🎯 Picked up pending project: {pending_project.project_slug} (ID: #{pending_project.id})"
                print(pickup_msg)
                manager.broadcast_sync(pickup_msg)
                asyncio.create_task(run_project_pipeline(pending_project.id))
            elif ticks % 12 == 0:  # Every 60 seconds (12 * 5s)
                time_str = time.strftime("%H:%M:%S")
                hb_msg = f"[{time_str}] [Worker] 💓 Heartbeat: Queue active, 0 pending tasks."
                manager.broadcast_sync(hb_msg)
                
        await asyncio.sleep(5)

