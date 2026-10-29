import os
import sys
import glob
import time
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

POSE_GALLERY_PATH = os.path.join(BASE_DIR, "server", "data", "pose_gallery.json")
RECIPES_DIR = os.path.join(BASE_DIR, "server", "data", "recipes")
os.makedirs(RECIPES_DIR, exist_ok=True)

class PoseSlot(BaseModel):
    slot_id: Optional[str] = None
    pose_id: str
    name: str
    category: str
    angle: str = "oblique"
    beats: int = 4
    seconds: float = 2.0
    dynamic_prompt: Optional[str] = None
    tags: Optional[List[str]] = None
    preview_urls: Optional[dict] = None

class ChoreographyRecipe(BaseModel):
    recipe_id: Optional[str] = None
    title: str = "自由创意舞蹈编排"
    creator: str = "AI Choreographer"
    style: str = "kpop"
    bpm: int = 128
    aspect_ratio: str = "9:16"
    sequence: List[PoseSlot]
    created_at: Optional[float] = None

@router.get("/poses")
def get_pose_gallery(
    category: Optional[str] = "all",
    angle: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    """
    动作知识库检索接口 (基于 ai-pose-gallery-zh 5视角 4阶段体系)
    """
    if not os.path.exists(POSE_GALLERY_PATH):
        raise HTTPException(status_code=404, detail="Pose gallery database not found")
        
    try:
        with open(POSE_GALLERY_PATH, "r", encoding="utf-8") as f:
            gallery_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read pose gallery: {e}")

    categories = gallery_data.get("categories", [])
    angles = gallery_data.get("angles", [])
    all_poses = gallery_data.get("poses", [])

    filtered_poses = []
    for pose in all_poses:
        # 分类筛选
        if category and category != "all" and pose.get("category") != category:
            continue
        # 视角筛选
        if angle and angle not in pose.get("available_angles", []):
            continue
        # 标签筛选
        if tag and tag not in pose.get("tags", []):
            continue
        # 关键词搜索 (匹配名称、标签或动势描述)
        if search:
            s = search.lower()
            name_match = s in pose.get("name", "").lower()
            tag_match = any(s in t.lower() for t in pose.get("tags", []))
            prompt_match = s in pose.get("dynamic_prompt", "").lower()
            if not (name_match or tag_match or prompt_match):
                continue
        
        filtered_poses.append(pose)

    return {
        "version": gallery_data.get("version", "2.0"),
        "total": len(all_poses),
        "filtered_count": len(filtered_poses),
        "categories": categories,
        "angles": angles,
        "poses": filtered_poses
    }

@router.post("/recipe")
def save_recipe(recipe: ChoreographyRecipe):
    """
    保存编舞配方并生成唯一 recipe_id 与 3:4 分享卡数据
    """
    rec_id = recipe.recipe_id or f"rec_{uuid.uuid4().hex[:8]}"
    recipe.recipe_id = rec_id
    recipe.created_at = time.time()
    
    file_path = os.path.join(RECIPES_DIR, f"{rec_id}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(recipe.dict(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {e}")

    # 计算总时长与动作拍数统计
    total_sec = sum(slot.seconds for slot in recipe.sequence)
    total_beats = sum(slot.beats for slot in recipe.sequence)
    
    return {
        "recipe_id": rec_id,
        "title": recipe.title,
        "total_duration": total_sec,
        "total_beats": total_beats,
        "bpm": recipe.bpm,
        "pose_count": len(recipe.sequence),
        "share_url": f"/dance?recipe_id={rec_id}",
        "message": "编舞配方保存成功！可用于社交裂变分享与一键同款"
    }

@router.get("/recipe/{recipe_id}")
def get_recipe(recipe_id: str):
    """
    读取指定编舞配方 (用于一键同款导入)
    """
    file_path = os.path.join(RECIPES_DIR, f"{recipe_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load recipe: {e}")

def run_choreographed_pipeline(
    task_id: str,
    input_image_path: str,
    sequence: List[dict],
    duration: int,
    style: str,
    bpm: int,
    prompt_desc: Optional[str],
    enable_jianying_draft: bool,
    tenant_id: str,
    selected_view_index: Optional[int],
    aspect_ratio: str
):
    try:
        dance_tasks[task_id]["status"] = "processing"
        dance_tasks[task_id]["progress"] = 10
        dance_tasks[task_id]["message"] = "Universal N-view adaptive perception & slicing..."
        
        output_mp4 = os.path.join(OUT_DIR, f"{task_id}_choreographed_{duration}s.mp4")
        script_path = os.path.join(BASE_DIR, ".agents", "skills", "character-dance-video", "scripts", "dance_pipeline_pro.py")
        
        # 将编舞动作序列合成为复合提示词与分镜描述
        seq_prompts = []
        for idx, item in enumerate(sequence):
            p_name = item.get("name", f"Pose_{idx+1}")
            p_angle = item.get("angle", "oblique")
            p_prompt = item.get("dynamic_prompt", "")
            seq_prompts.append(f"Shot {idx+1} ({p_angle} view): {p_prompt}")
            
        choreographed_prompt = "; ".join(seq_prompts)
        if prompt_desc:
            choreographed_prompt = f"{prompt_desc}. Sequence: {choreographed_prompt}"

        cmd = [
            "python3", "-u", script_path,
            "--input-image", input_image_path,
            "--duration", str(duration),
            "--style", style,
            "--bpm", str(bpm),
            "--output", output_mp4,
            "--tenant-id", tenant_id,
            "--aspect-ratio", aspect_ratio,
            "--prompt-desc", choreographed_prompt
        ]
        if selected_view_index is not None:
            cmd.extend(["--selected-view-index", str(selected_view_index)])
            
        dance_tasks[task_id]["progress"] = 30
        dance_tasks[task_id]["message"] = f"Synthesizing choreographed dance ({len(sequence)} poses)..."

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=BASE_DIR)
        for line in process.stdout:
            clean_line = line.strip()
            print(f"[ChoreoTask-{task_id[:6]}] {clean_line}", flush=True)
            if "Step 2" in clean_line:
                dance_tasks[task_id]["progress"] = 40
            elif "Step 5" in clean_line:
                dance_tasks[task_id]["progress"] = 80
            elif "Step 6" in clean_line:
                dance_tasks[task_id]["progress"] = 90

        process.wait()

        if process.returncode == 0 and os.path.exists(output_mp4):
            dance_tasks[task_id]["status"] = "completed"
            dance_tasks[task_id]["progress"] = 100
            dance_tasks[task_id]["message"] = "自由编舞视频生成成功！"
            dance_tasks[task_id]["video_url"] = f"/media/out/web_dance_studio/{os.path.basename(output_mp4)}"
            dance_tasks[task_id]["video_path"] = output_mp4

            # 导出剪映工程草稿 (双模交付)
            if enable_jianying_draft:
                try:
                    sys.path.append(BASE_DIR)
                    from shared_tools.drafts.jianying_exporter import JianyingExporter
                    exporter = JianyingExporter()
                    draft_shots = []
                    # 按 sequence 拆分草稿镜头槽位
                    slot_dur = max(2.0, float(duration) / max(1, len(sequence)))
                    for idx, s_item in enumerate(sequence):
                        draft_shots.append({
                            "id": f"choreo_shot_{idx+1}",
                            "video_path": output_mp4,
                            "audio_path": None,
                            "duration": slot_dur,
                            "subtitle": s_item.get("name", f"动作 {idx+1}"),
                            "enable_slow_zoom": True
                        })
                    
                    draft_res = exporter.export_project_draft(
                        project_name=f"Dance_{task_id[:8]}",
                        shots_data=draft_shots,
                        output_dir=OUT_DIR
                    )
                    if draft_res and draft_res.get("zip_path"):
                        zip_rel = os.path.relpath(draft_res["zip_path"], os.path.join(BASE_DIR, "out"))
                        dance_tasks[task_id]["jianying_draft_zip"] = f"/media/out/{zip_rel}"
                        dance_tasks[task_id]["jianying_synced"] = draft_res.get("synced_to_local", False)
                        print(f"[ChoreoTask-{task_id[:6]}] Exported JianYing draft ZIP: {dance_tasks[task_id]['jianying_draft_zip']}")
                except Exception as de:
                    print(f"[ChoreoTask-{task_id[:6]}] JianYing draft export notice: {de}")
        else:
            dance_tasks[task_id]["status"] = "failed"
            dance_tasks[task_id]["message"] = f"Generation failed (code {process.returncode})"
    except Exception as e:
        dance_tasks[task_id]["status"] = "failed"
        dance_tasks[task_id]["message"] = str(e)

@router.post("/choreograph")
async def choreograph_dance(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    sequence_json: str = Form(...),
    style: str = Form("kpop"),
    bpm: int = Form(128),
    prompt_desc: Optional[str] = Form(None),
    enable_jianying_draft: bool = Form(True),
    tenant_id: str = Form("default"),
    selected_view_index: Optional[int] = Form(None),
    aspect_ratio: str = Form("9:16")
):
    """
    自由编舞执行接口：接收多动作序列时间轴并生成成品舞蹈与剪映双模草稿
    """
    try:
        sequence = json.loads(sequence_json)
        if not isinstance(sequence, list) or len(sequence) == 0:
            raise HTTPException(status_code=400, detail="Sequence must be a non-empty list of pose slots")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid sequence_json format: {e}")

    task_id = uuid.uuid4().hex
    ext = os.path.splitext(image.filename)[1] or ".png"
    saved_img_path = os.path.join(OUT_DIR, f"{task_id}_choreo_input{ext}")
    
    with open(saved_img_path, "wb") as f:
        content = await image.read()
        f.write(content)

    total_duration = int(round(sum(float(item.get("seconds", 2.0)) for item in sequence)))
    total_duration = max(10, min(60, total_duration))

    dance_tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "message": f"Choreography task submitted ({len(sequence)} poses, {total_duration}s). Waiting to start...",
        "duration": total_duration,
        "style": style,
        "sequence": sequence,
        "bpm": bpm,
        "tenant_id": tenant_id,
        "selected_view_index": selected_view_index,
        "aspect_ratio": aspect_ratio,
        "video_url": None,
        "jianying_draft_zip": None
    }

    background_tasks.add_task(
        run_choreographed_pipeline,
        task_id,
        saved_img_path,
        sequence,
        total_duration,
        style,
        bpm,
        prompt_desc,
        enable_jianying_draft,
        tenant_id,
        selected_view_index,
        aspect_ratio
    )
    return {"task_id": task_id, "status": "queued", "duration": total_duration, "poses_count": len(sequence)}

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = dance_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

