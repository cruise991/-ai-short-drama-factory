from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
from models.database import get_session, Project
from datetime import datetime
import os
import glob
import asyncio
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Global dictionary to hold asyncio.Future objects for pending inputs
PENDING_INPUTS = {}

class CreateProjectRequest(BaseModel):
    goal: str
    format_type: str = "vertical"
    branch_type: str = "short_drama"
    selected_ip: Optional[str] = None
    vibe: Optional[str] = None
    trend_enabled: bool = False

@router.post("/", response_model=Project)
def create_project(
    payload: Optional[CreateProjectRequest] = None,
    # Keep query parameters as fallback for backward compatibility
    goal: Optional[str] = None, 
    format_type: str = "vertical", 
    branch_type: str = "short_drama",
    selected_ip: Optional[str] = None,
    vibe: Optional[str] = None,
    trend_enabled: bool = False,
    session: Session = Depends(get_session)
):
    import re
    # Resolve values from JSON payload first, then fallback to query parameters
    req_goal = (payload.goal if payload else goal) or ""
    req_format = (payload.format_type if payload else format_type) or "vertical"
    req_branch = (payload.branch_type if payload else branch_type) or "short_drama"
    req_ip = payload.selected_ip if payload else selected_ip
    req_vibe = payload.vibe if payload else vibe
    req_trend = payload.trend_enabled if payload else trend_enabled

    # Create a clean slug from the goal
    clean_goal = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '_', req_goal.lower())[:30].strip('_')
    if not clean_goal:
        slug = f"project_{int(datetime.utcnow().timestamp())}"
    else:
        slug = f"{clean_goal}_{int(datetime.utcnow().timestamp())}"
        
    project = Project(
        project_slug=slug,
        goal=req_goal,
        format_type=req_format,
        branch_type=req_branch,
        selected_ip=req_ip,
        vibe=req_vibe,
        trend_enabled=req_trend,
        status="Pending"
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/", response_model=List[Project])
def get_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    return projects

class UserInput(BaseModel):
    message: str

@router.get("/{project_id}/internal_wait_input")
async def internal_wait_input(project_id: int):
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    PENDING_INPUTS[project_id] = future
    
    # Wait until the future is resolved by submit_input
    text = await future
    del PENDING_INPUTS[project_id]
    return {"text": text}

@router.post("/{project_id}/input")
def submit_input(project_id: int, user_input: UserInput):
    if project_id in PENDING_INPUTS:
        future = PENDING_INPUTS[project_id]
        if not future.done():
            future.set_result(user_input.message)
        return {"success": True}
    return {"success": False, "reason": "No pending input"}

@router.post("/{project_id}/approve")
def approve_project(project_id: int):
    """One-click approval for script/storyboard or current phase."""
    if project_id in PENDING_INPUTS:
        future = PENDING_INPUTS[project_id]
        if not future.done():
            future.set_result("ok")
        return {"success": True, "message": "Phase approved successfully"}
    return {"success": False, "reason": "Project is not currently awaiting manual approval"}

@router.post("/{project_id}/reject")
def reject_project(project_id: int, user_input: UserInput):
    """Reject and submit critical correction feedback to QA & Planning."""
    if project_id in PENDING_INPUTS:
        future = PENDING_INPUTS[project_id]
        if not future.done():
            future.set_result(user_input.message)
        return {"success": True, "message": "Feedback submitted successfully"}
    return {"success": False, "reason": "Project is not currently awaiting manual approval"}

@router.get("/{slug}/detail")
def get_project_detail(slug: str, session: Session = Depends(get_session)):
    """Fetch structured pipeline status, storyboard script, and feedback states."""
    project = session.exec(select(Project).where(Project.project_slug == slug)).first()
    if not project:
        # Fallback: check if slug matches without timestamp suffix
        project = session.exec(select(Project).where(Project.project_slug.like(f"{slug}%"))).first()
        
    base_dir = get_base_dir()
    runs_dir = os.path.join(base_dir, "projects", slug, "runs")
    
    ticket_data = {}
    storyboard_text = ""
    latest_run_id = None
    
    if os.path.exists(runs_dir):
        run_ids = sorted([d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))], reverse=True)
        if run_ids:
            latest_run_id = run_ids[0]
            run_path = os.path.join(runs_dir, latest_run_id)
            
            # Read ticket
            t_path = os.path.join(run_path, "00_task_ticket.json")
            if os.path.exists(t_path):
                try:
                    with open(t_path, "r", encoding="utf-8") as f:
                        ticket_data = json.load(f)
                except Exception:
                    pass
                    
            # Read storyboard script if available
            sb_path = os.path.join(run_path, "01_storyboards_scripts", "01_storyboard.md")
            if os.path.exists(sb_path):
                try:
                    with open(sb_path, "r", encoding="utf-8") as f:
                        storyboard_text = f.read()
                except Exception:
                    pass
                    
    is_waiting_approval = False
    project_id = project.id if project else None
    if project_id and project_id in PENDING_INPUTS:
        is_waiting_approval = True
        
    return {
        "project": project,
        "latest_run_id": latest_run_id,
        "ticket": ticket_data,
        "storyboard": storyboard_text,
        "is_waiting_approval": is_waiting_approval,
        "current_status": ticket_data.get("status", project.status if project else "Unknown")
    }


def get_base_dir() -> str:
    if os.path.exists("/workspace/out"):
        return "/workspace"
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@router.get("/{slug}/assets")
def get_assets(slug: str):
    base_dir = get_base_dir()
    out_dirs = [
        os.path.join(base_dir, "out", slug),
        os.path.join(os.path.dirname(base_dir), "out", slug),
    ]
    runs_dirs = [
        os.path.join(base_dir, "projects", slug, "runs"),
        os.path.join(os.path.dirname(base_dir), "projects", slug, "runs"),
    ]
    
    videos = []
    images = []
    seen_videos = set()
    seen_images = set()
    
    # Check out_dirs for videos
    for out_dir in out_dirs:
        if os.path.exists(out_dir):
            for f in glob.glob(f"{out_dir}/*.mp4"):
                fname = os.path.basename(f)
                if fname not in seen_videos:
                    seen_videos.add(fname)
                    videos.append(f"/media/out/{slug}/{fname}")
            
    # Check runs_dirs for images (storyboards)
    for runs_dir in runs_dirs:
        if os.path.exists(runs_dir):
            for run_id in os.listdir(runs_dir):
                run_path = os.path.join(runs_dir, run_id)
                if os.path.isdir(run_path):
                    img_path = os.path.join(run_path, "assets", "02_storyboards")
                    if os.path.exists(img_path):
                        for f in glob.glob(f"{img_path}/*.*"):
                            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                                fname = os.path.basename(f)
                                if (run_id, fname) not in seen_images:
                                    seen_images.add((run_id, fname))
                                    images.append(f"/media/projects/{slug}/runs/{run_id}/assets/02_storyboards/{fname}")
                            
    return {
        "videos": videos,
        "images": images
    }
