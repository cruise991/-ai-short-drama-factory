import os
import json
import time
import sys
from orchestrator import process_single_run

if __name__ == "__main__":
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if workspace_dir not in sys.path:
        sys.path.insert(0, workspace_dir)
    project_name = "test_c007_nana"
    projects_dir = os.path.join(workspace_dir, "projects")
    project_dir = os.path.join(projects_dir, project_name)
    run_id = time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(project_dir, "runs", run_id)
    os.makedirs(run_dir, exist_ok=True)

    ticket_path = os.path.join(run_dir, "00_task_ticket.json")
    ticket = {
        "goal": "单集视频 - C007_Nana 测试",
        "workflow_type": "dance_video",
        "visual_style_directive": "",
        "trend_context": "未启用热点",
        "duration": 25,
        "module_params": {
            "character_id": "C007_Nana",
            "scene_cat": "outdoor",
            "combo_strategy": "Strategy_1",
            "base_template": "moonlight_dance"
        },
        "language": "中文",
        "aspect_ratio": "9:16",
        "project_name": project_name,
        "status": "Pending",
        "director_confirmed": False,
        "workflow_start_time": time.time()
    }

    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)

    print(f"Created test ticket at {ticket_path}")
    print("Running orchestrator flow...")

    process_single_run(ticket_path, run_dir, workspace_dir)
