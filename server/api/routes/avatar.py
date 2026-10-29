from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel

from models.database import (
    get_session,
    Avatar,
    AvatarStatus,
    SceneVideo
)

router = APIRouter(prefix="/avatars", tags=["avatars"])

class AvatarCreateReq(BaseModel):
    name: str
    tenant_id: Optional[str] = "default"
    avatar_type: Optional[str] = "2d_nerf"
    preview_url: Optional[str] = None
    model_path: Optional[str] = None
    voice_id: Optional[str] = "zh-CN-XiaoxiaoNeural"
    config_json: Optional[str] = "{}"
    status: Optional[str] = AvatarStatus.ACTIVE.value

class AvatarUpdateReq(BaseModel):
    name: Optional[str] = None
    preview_url: Optional[str] = None
    voice_id: Optional[str] = None
    config_json: Optional[str] = None
    status: Optional[str] = None

class SceneCreateReq(BaseModel):
    title: str
    tenant_id: Optional[str] = "default"
    video_url: str
    duration: Optional[float] = 0.0
    resolution: Optional[str] = "1080x1920"
    is_loop: Optional[bool] = True

@router.get("", response_model=List[Avatar])
def list_avatars(
    tenant_id: Optional[str] = Query("default"),
    status: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    query = select(Avatar).where(Avatar.tenant_id == tenant_id)
    if status:
        query = query.where(Avatar.status == status)
    return session.exec(query).all()

@router.post("", response_model=Avatar, status_code=status.HTTP_201_CREATED)
def create_avatar(
    req: AvatarCreateReq,
    session: Session = Depends(get_session)
):
    avatar = Avatar(
        name=req.name,
        tenant_id=req.tenant_id or "default",
        avatar_type=req.avatar_type or "2d_nerf",
        preview_url=req.preview_url,
        model_path=req.model_path,
        voice_id=req.voice_id or "zh-CN-XiaoxiaoNeural",
        config_json=req.config_json or "{}",
        status=req.status or AvatarStatus.ACTIVE.value
    )
    session.add(avatar)
    session.commit()
    session.refresh(avatar)
    return avatar

# ----------------- Scenes (Must be placed before /{avatar_id}) -----------------

@router.get("/scenes", response_model=List[SceneVideo])
@router.get("/scenes/list", response_model=List[SceneVideo])
def list_scenes(
    tenant_id: Optional[str] = Query("default"),
    session: Session = Depends(get_session)
):
    query = select(SceneVideo).where(SceneVideo.tenant_id == tenant_id)
    return session.exec(query).all()

@router.post("/scenes", response_model=SceneVideo, status_code=status.HTTP_201_CREATED)
@router.post("/scenes/create", response_model=SceneVideo, status_code=status.HTTP_201_CREATED)
def create_scene(
    req: SceneCreateReq,
    session: Session = Depends(get_session)
):
    scene = SceneVideo(
        title=req.title,
        tenant_id=req.tenant_id or "default",
        video_url=req.video_url,
        duration=req.duration or 0.0,
        resolution=req.resolution or "1080x1920",
        is_loop=req.is_loop if req.is_loop is not None else True
    )
    session.add(scene)
    session.commit()
    session.refresh(scene)
    return scene

# ----------------- Parameterized Avatar Routes -----------------

@router.get("/{avatar_id}", response_model=Avatar)
def get_avatar(avatar_id: int, session: Session = Depends(get_session)):
    avatar = session.get(Avatar, avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar ID {avatar_id} not found")
    return avatar

@router.put("/{avatar_id}", response_model=Avatar)
def update_avatar(
    avatar_id: int,
    req: AvatarUpdateReq,
    session: Session = Depends(get_session)
):
    avatar = session.get(Avatar, avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar ID {avatar_id} not found")

    if req.name is not None:
        avatar.name = req.name
    if req.preview_url is not None:
        avatar.preview_url = req.preview_url
    if req.voice_id is not None:
        avatar.voice_id = req.voice_id
    if req.config_json is not None:
        avatar.config_json = req.config_json
    if req.status is not None:
        avatar.status = req.status
    avatar.updated_at = datetime.utcnow()

    session.add(avatar)
    session.commit()
    session.refresh(avatar)
    return avatar

@router.delete("/{avatar_id}")
def delete_avatar(avatar_id: int, hard_delete: bool = False, session: Session = Depends(get_session)):
    avatar = session.get(Avatar, avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar ID {avatar_id} not found")
    
    if hard_delete:
        session.delete(avatar)
        session.commit()
        return {"status": "ok", "message": f"Avatar {avatar_id} permanently deleted"}
    else:
        avatar.status = AvatarStatus.ARCHIVED.value
        session.add(avatar)
        session.commit()
        session.refresh(avatar)
        return {"status": "ok", "message": f"Avatar {avatar_id} archived successfully"}
