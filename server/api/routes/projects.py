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

@router.post("/", response_model=Project)
def create_project(
    goal: str, 
    format_type: str = "vertical", 
    branch_type: str = "short_drama",
    selected_ip: Optional[str] = None,
    vibe: Optional[str] = None,
    trend_enabled: bool = False,
    session: Session = Depends(get_session)
):
    import re
    # Create a simple slug from the goal
    slug = re.sub(r'[^a-zA-Z0-9]', '_', goal.lower())[:30].strip('_')
    if not slug:
        slug = f"project_{int(datetime.utcnow().timestamp())}"
    else:
        slug = f"{slug}_{int(datetime.utcnow().timestamp())}"
        
    project = Project(
        project_slug=slug,
        goal=goal,
        format_type=format_type,
        branch_type=branch_type,
        selected_ip=selected_ip,
        vibe=vibe,
        trend_enabled=trend_enabled,
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

@router.get("/{slug}/assets")
def get_assets(slug: str):
    # Base paths
    out_dir = f"/workspace/out/{slug}"
    runs_dir = f"/workspace/projects/{slug}/runs"
    
    videos = []
    images = []
    
    # Check out_dir for videos
    if os.path.exists(out_dir):
        for f in glob.glob(f"{out_dir}/*.mp4"):
            videos.append(f"/media/out/{slug}/{os.path.basename(f)}")
            
    # Check runs_dir for images (storyboards)
    if os.path.exists(runs_dir):
        # run_ids
        for run_id in os.listdir(runs_dir):
            run_path = os.path.join(runs_dir, run_id)
            if os.path.isdir(run_path):
                img_path = os.path.join(run_path, "assets", "02_storyboards")
                if os.path.exists(img_path):
                    for f in glob.glob(f"{img_path}/*.*"):
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                            images.append(f"/media/projects/{slug}/runs/{run_id}/assets/02_storyboards/{os.path.basename(f)}")
                            
    return {
        "videos": videos,
        "images": images
    }
