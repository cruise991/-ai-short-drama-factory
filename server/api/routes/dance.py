import os
import glob
import json
import uuid
import asyncio
import subprocess
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/dance", tags=["dance"])

# Auto-adapt for Docker (/workspace) or local host filesystem
if os.path.exists("/workspace/assets/dance/07_templates"):
    BASE_DIR = "/workspace"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

TEMPLATES_DIR = os.path.join(BASE_DIR, "assets", "dance", "07_templates")
OUT_DIR = os.path.join(BASE_DIR, "out", "web_dance_studio")
os.makedirs(OUT_DIR, exist_ok=True)

# In-memory task tracking
dance_tasks = {}

class DanceTemplate(BaseModel):
    dance_id: str
    name: str
    bpm: str
    duration_range: List[int]
    tags: List[str]
    stats: Optional[dict] = None
    timeline: Optional[List[dict]] = None

@router.get("/templates", response_model=List[DanceTemplate])
def get_dance_templates():
    templates = []
    if not os.path.exists(TEMPLATES_DIR):
        return []
    
    files = glob.glob(os.path.join(TEMPLATES_DIR, "*.json"))
    for fpath in sorted(files):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                templates.append(DanceTemplate(
                    dance_id=data.get("dance_id", os.path.splitext(os.path.basename(fpath))[0]),
                    name=data.get("name", "未知舞蹈"),
                    bpm=str(data.get("bpm", "120")),
                    duration_range=data.get("duration_range", [15, 30]),
                    tags=data.get("tags", []),
                    stats=data.get("stats", {}),
                    timeline=data.get("timeline", [])
                ))
        except Exception as e:
            print(f"Error reading template {fpath}: {e}")
    return templates

def run_dance_generation(task_id: str, input_image_path: str, duration: int, style: str, prompt_desc: Optional[str], bpm: int):
    try:
        dance_tasks[task_id]["status"] = "processing"
        dance_tasks[task_id]["progress"] = 10
        dance_tasks[task_id]["message"] = "Analyzing character features and uploading to cloud..."
        
        output_mp4 = os.path.join(OUT_DIR, f"{task_id}_dance_{duration}s.mp4")
        script_path = os.path.join(BASE_DIR, ".agents", "skills", "character-dance-video", "scripts", "dance_pipeline_pro.py")
        
        cmd = [
            "python3", "-u", script_path,
            "--input-image", input_image_path,
            "--duration", str(duration),
            "--style", style,
            "--bpm", str(bpm),
            "--output", output_mp4
        ]
        if prompt_desc:
            cmd.extend(["--prompt-desc", prompt_desc])
        
        dance_tasks[task_id]["progress"] = 25
        dance_tasks[task_id]["message"] = "Generating sequential dance shots with keyframes loop closure..."
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=BASE_DIR)
        for line in process.stdout:
            print(f"[DanceTask-{task_id[:6]}] {line.strip()}")
            if "Generating sequential" in line or "Shot " in line:
                dance_tasks[task_id]["progress"] = min(85, dance_tasks[task_id]["progress"] + 15)
                dance_tasks[task_id]["message"] = line.strip()
            elif "Step 5" in line or "Audio Director" in line:
                dance_tasks[task_id]["progress"] = 90
                dance_tasks[task_id]["message"] = "Synthesizing synced producer BGM..."
            elif "Step 6" in line or "Muxing" in line:
                dance_tasks[task_id]["progress"] = 95
                dance_tasks[task_id]["message"] = "Two-step safe video-audio muxing..."
        
        process.wait()
        if process.returncode == 0 and os.path.exists(output_mp4):
            dance_tasks[task_id]["status"] = "completed"
            dance_tasks[task_id]["progress"] = 100
            dance_tasks[task_id]["message"] = "Dance video generated successfully!"
            dance_tasks[task_id]["video_url"] = f"/media/out/web_dance_studio/{os.path.basename(output_mp4)}"
            dance_tasks[task_id]["video_path"] = output_mp4
        else:
            dance_tasks[task_id]["status"] = "failed"
            dance_tasks[task_id]["message"] = "Generation process failed. Check server logs."
    except Exception as e:
        dance_tasks[task_id]["status"] = "failed"
        dance_tasks[task_id]["message"] = str(e)

@router.post("/generate")
async def generate_dance_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    duration: int = Form(20),
    style: str = Form("kpop"),
    prompt_desc: Optional[str] = Form(None),
    bpm: int = Form(128)
):
    task_id = uuid.uuid4().hex
    ext = os.path.splitext(image.filename)[1] or ".png"
    saved_img_path = os.path.join(OUT_DIR, f"{task_id}_input{ext}")
    
    with open(saved_img_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    # Auto-link template settings if provided
    if template_id:
        t_path = os.path.join(TEMPLATES_DIR, f"{template_id}.json")
        if not os.path.exists(t_path) and not template_id.endswith(".json"):
            t_path = os.path.join(TEMPLATES_DIR, f"{template_id}.json")
        if os.path.exists(t_path):
            try:
                with open(t_path, "r", encoding="utf-8") as tf:
                    t_data = json.load(tf)
                    raw_bpm = t_data.get("bpm", "128")
                    if "-" in str(raw_bpm):
                        bpm = int(raw_bpm.split("-")[0].strip())
                    elif str(raw_bpm).isdigit():
                        bpm = int(raw_bpm)
            except Exception:
                pass
    
    dance_tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "message": "Task submitted. Waiting to start...",
        "duration": duration,
        "style": style,
        "template_id": template_id,
        "video_url": None
    }
    
    background_tasks.add_task(run_dance_generation, task_id, saved_img_path, duration, style, prompt_desc, bpm)
    return {"task_id": task_id, "status": "queued"}

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = dance_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
