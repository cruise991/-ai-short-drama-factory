import os
import sys
import glob
import json
import uuid
import asyncio
import subprocess
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/dance", tags=["dance"])

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

def run_dance_generation(
    task_id: str,
    input_image_path: str,
    duration: int,
    style: str,
    prompt_desc: Optional[str],
    bpm: int,
    template_id: Optional[str] = None,
    tenant_id: str = "default",
    selected_view_index: Optional[int] = None,
    aspect_ratio: str = "9:16"
):
    try:
        dance_tasks[task_id]["status"] = "processing"
        dance_tasks[task_id]["progress"] = 10
        dance_tasks[task_id]["message"] = "Universal N-view adaptive perception & slicing..."
        
        output_mp4 = os.path.join(OUT_DIR, f"{task_id}_dance_{duration}s.mp4")
        script_path = os.path.join(BASE_DIR, ".agents", "skills", "character-dance-video", "scripts", "dance_pipeline_pro.py")
        
        cmd = [
            "python3", "-u", script_path,
            "--input-image", input_image_path,
            "--duration", str(duration),
            "--style", style,
            "--bpm", str(bpm),
            "--output", output_mp4,
            "--tenant-id", tenant_id,
            "--aspect-ratio", aspect_ratio
        ]
        if prompt_desc:
            cmd.extend(["--prompt-desc", prompt_desc])
        if template_id:
            cmd.extend(["--template", template_id])
        if selected_view_index is not None:
            cmd.extend(["--selected-view-index", str(selected_view_index)])
        
        dance_tasks[task_id]["progress"] = 25
        dance_tasks[task_id]["message"] = "Generating sequential dance shots with keyframes loop closure..."
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=BASE_DIR)
        last_logs = []
        for line in process.stdout:
            clean_line = line.strip()
            print(f"[DanceTask-{task_id[:6]}] {clean_line}", flush=True)
            last_logs.append(clean_line)
            if len(last_logs) > 30:
                last_logs.pop(0)
            if "Step 1" in clean_line or "Universal N-View" in clean_line or "Perception" in clean_line:
                dance_tasks[task_id]["progress"] = 12
                dance_tasks[task_id]["message"] = "N-view adaptive perception & front-view anchoring..."
            elif "Step 2" in clean_line or "Vision" in clean_line or "360°" in clean_line:
                dance_tasks[task_id]["progress"] = 20
                dance_tasks[task_id]["message"] = "Extracting 360° multi-view knowledge graph & defenses..."
            elif "Generating sequential" in clean_line or "Shot " in clean_line:
                dance_tasks[task_id]["progress"] = min(85, max(25, dance_tasks[task_id]["progress"] + 15))
                dance_tasks[task_id]["message"] = clean_line
            elif "Step 5" in clean_line or "Audio Director" in clean_line:
                dance_tasks[task_id]["progress"] = 88
                dance_tasks[task_id]["message"] = "Synthesizing synced producer BGM..."
            elif "Step 6" in clean_line or "Muxing" in clean_line:
                dance_tasks[task_id]["progress"] = 92
                dance_tasks[task_id]["message"] = "Two-step safe video-audio muxing & sharpening..."
            elif "Step 7" in clean_line or "Face Enhance" in clean_line or "面部增强" in clean_line:
                dance_tasks[task_id]["progress"] = 96
                dance_tasks[task_id]["message"] = "HD face enhancement processing..."
        
        process.wait()
        if process.returncode == 0 and os.path.exists(output_mp4):
            dance_tasks[task_id]["status"] = "completed"
            dance_tasks[task_id]["progress"] = 100
            dance_tasks[task_id]["message"] = "Dance video generated successfully!"
            dance_tasks[task_id]["video_url"] = f"/media/out/web_dance_studio/{os.path.basename(output_mp4)}"
            dance_tasks[task_id]["video_path"] = output_mp4
        else:
            dance_tasks[task_id]["status"] = "failed"
            error_tail = "\n".join(last_logs[-5:]) if last_logs else "No process output"
            dance_tasks[task_id]["message"] = f"Generation failed (code {process.returncode}): {error_tail}"
    except Exception as e:
        dance_tasks[task_id]["status"] = "failed"
        dance_tasks[task_id]["message"] = str(e)

@router.post("/analyze-views")
async def analyze_multiviews(
    image: UploadFile = File(...),
    tenant_id: str = Form("default")
):
    """
    SaaS Multi-tenant Viewpoint Auto-Detection Endpoint.
    Perceives N viewpoints, performs anti-bleed slicing, and returns view candidates.
    """
    temp_id = uuid.uuid4().hex
    ext = os.path.splitext(image.filename)[1] or ".png"
    temp_dir = os.path.join(OUT_DIR, "tenants", tenant_id, "previews", temp_id)
    os.makedirs(temp_dir, exist_ok=True)
    temp_img_path = os.path.join(temp_dir, f"input{ext}")
    
    with open(temp_img_path, "wb") as f:
        content = await image.read()
        f.write(content)
        
    try:
        sys.path.append(os.path.join(BASE_DIR, ".agents", "skills", "character-dance-video", "scripts"))
        from multi_view_adapter import MultiViewAdapter
        adapter = MultiViewAdapter(debug=False)
        result = adapter.run_pipeline(temp_img_path, temp_dir, tenant_id=tenant_id, project_id=temp_id)
        
        # Convert local paths to relative web-accessible media URLs
        for v in result["views"]:
            rel_path = os.path.relpath(v["path"], os.path.join(BASE_DIR, "out"))
            v["preview_url"] = f"/media/out/{rel_path}"
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze multi-view image: {e}")

@router.post("/generate")
async def generate_dance_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    duration: int = Form(20),
    style: str = Form("kpop"),
    prompt_desc: Optional[str] = Form(None),
    bpm: int = Form(128),
    tenant_id: str = Form("default"),
    selected_view_index: Optional[int] = Form(None),
    aspect_ratio: str = Form("9:16")
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
        "tenant_id": tenant_id,
        "selected_view_index": selected_view_index,
        "aspect_ratio": aspect_ratio,
        "video_url": None
    }
    
    background_tasks.add_task(
        run_dance_generation,
        task_id,
        saved_img_path,
        duration,
        style,
        prompt_desc,
        bpm,
        template_id,
        tenant_id,
        selected_view_index,
        aspect_ratio
    )
    return {"task_id": task_id, "status": "queued"}

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = dance_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
