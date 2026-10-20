import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlmodel import Session, select
from pydantic import BaseModel

from models.database import (
    get_session,
    LiveSession,
    LiveSessionStatus,
    LiveMessage,
    LiveProduct,
    Product,
    Avatar
)
from services.live_orchestrator import LiveOrchestrator
from core.compliance import audit_text_compliance
from core.watermark import WatermarkConfig, audit_avatar_licensing

router = APIRouter(prefix="/live", tags=["live"])

# 全局内存会话管理器
ACTIVE_ORCHESTRATORS: Dict[int, LiveOrchestrator] = {}
WS_ROOM_CONNECTIONS: Dict[int, List[WebSocket]] = {}

class StartLiveReq(BaseModel):
    title: str
    tenant_id: Optional[str] = "default"
    room_id: str
    avatar_id: Optional[int] = None
    scene_video_id: Optional[int] = None

class StopLiveReq(BaseModel):
    session_id: int

class DanmakuSendReq(BaseModel):
    session_id: int
    user_name: Optional[str] = "热心观众"
    content: str

class InsertScriptReq(BaseModel):
    session_id: int
    content: str
    priority: Optional[bool] = True

class SwitchProductReq(BaseModel):
    session_id: int
    product_id: int

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_live_session(
    req: StartLiveReq,
    session: Session = Depends(get_session)
):
    # 肖像授权合规前置审计
    if req.avatar_id:
        avatar = session.get(Avatar, req.avatar_id)
        if not avatar:
            if req.avatar_id == 1:
                avatar = Avatar(
                    id=1,
                    name="小婉 (官方合规主播)",
                    avatar_type="lingcast_live",
                    status="active",
                    config_json='{"licensing_status": "verified"}'
                )
                session.add(avatar)
                session.commit()
                session.refresh(avatar)
            else:
                raise HTTPException(status_code=404, detail=f"Avatar {req.avatar_id} not found")

        is_valid, reason = audit_avatar_licensing(avatar)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"数字人肖像授权合规审查未通过: {reason}"
            )

    stream_key = f"live_{uuid.uuid4().hex[:12]}"
    
    # 查找是否已有该 room_id 的 session 记录 (避免 UNIQUE constraint failed)
    existing_sess = session.exec(select(LiveSession).where(LiveSession.room_id == req.room_id)).first()
    if existing_sess:
        live_sess = existing_sess
        live_sess.title = req.title
        live_sess.tenant_id = req.tenant_id or "default"
        live_sess.avatar_id = req.avatar_id
        live_sess.scene_video_id = req.scene_video_id
        live_sess.status = LiveSessionStatus.STREAMING.value
        live_sess.stream_key = stream_key
        live_sess.rtmp_url = f"rtmp://localhost:1935/live/{stream_key}"
        live_sess.http_flv_url = f"http://localhost:8085/live/{stream_key}.flv"
        live_sess.started_at = datetime.utcnow()
        live_sess.ended_at = None
        live_sess.viewer_count = 1
        session.add(live_sess)
        session.commit()
        session.refresh(live_sess)
    else:
        live_sess = LiveSession(
            title=req.title,
            tenant_id=req.tenant_id or "default",
            room_id=req.room_id,
            avatar_id=req.avatar_id,
            scene_video_id=req.scene_video_id,
            status=LiveSessionStatus.STREAMING.value,
            stream_key=stream_key,
            rtmp_url=f"rtmp://localhost:1935/live/{stream_key}",
            http_flv_url=f"http://localhost:8085/live/{stream_key}.flv",
            started_at=datetime.utcnow(),
            viewer_count=1
        )
        session.add(live_sess)
        session.commit()
        session.refresh(live_sess)

    # 启动编排实例 (注入法定 AI 水印配置)
    orchestrator = LiveOrchestrator(
        session_id=live_sess.id,
        room_id=req.room_id,
        avatar_id=req.avatar_id or 1,
        stream_key=stream_key,
        watermark_config=WatermarkConfig()
    )
    await orchestrator.start_streaming()
    ACTIVE_ORCHESTRATORS[live_sess.id] = orchestrator

    return {
        "status": "ok",
        "session_id": live_sess.id,
        "room_id": live_sess.room_id,
        "stream_key": stream_key,
        "rtmp_url": live_sess.rtmp_url,
        "http_flv_url": live_sess.http_flv_url,
        "session_status": live_sess.status
    }

@router.post("/stop")
async def stop_live_session(
    req: StopLiveReq,
    session: Session = Depends(get_session)
):
    live_sess = session.get(LiveSession, req.session_id)
    if not live_sess:
        raise HTTPException(status_code=404, detail=f"LiveSession {req.session_id} not found")

    live_sess.status = LiveSessionStatus.FINISHED.value
    live_sess.ended_at = datetime.utcnow()
    session.add(live_sess)
    session.commit()

    if req.session_id in ACTIVE_ORCHESTRATORS:
        await ACTIVE_ORCHESTRATORS[req.session_id].stop_streaming()
        del ACTIVE_ORCHESTRATORS[req.session_id]

    return {"status": "ok", "message": f"LiveSession {req.session_id} terminated."}

@router.get("/status")
def get_live_status(
    session_id: Optional[int] = Query(None),
    room_id: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    # 检查是否有正在推流的全局活跃会话
    streaming_sess = session.exec(
        select(LiveSession).where(LiveSession.status == LiveSessionStatus.STREAMING.value).order_by(LiveSession.id.desc())
    ).first()

    query = select(LiveSession)
    if session_id:
        query = query.where(LiveSession.id == session_id)
    elif room_id:
        query = query.where(LiveSession.room_id == room_id)
    else:
        # Default to latest active or created
        if streaming_sess:
            query = query.where(LiveSession.id == streaming_sess.id)
        else:
            query = query.order_by(LiveSession.id.desc())

    live_sess = session.exec(query).first()
    if not live_sess:
        return {
            "status": "idle",
            "message": "No active live session found.",
            "active_streaming_room": streaming_sess.room_id if streaming_sess else None,
            "active_session_id": streaming_sess.id if streaming_sess else None,
        }

    is_running = live_sess.id in ACTIVE_ORCHESTRATORS and ACTIVE_ORCHESTRATORS[live_sess.id].is_running
    
    # 提取当前出镜主播信息
    avatar_data = None
    if live_sess.avatar_id:
        av = session.get(Avatar, live_sess.avatar_id)
        if av:
            avatar_data = {
                "id": av.id,
                "name": av.name,
                "avatar_type": av.avatar_type,
                "voice_id": av.voice_id,
                "image_url": av.preview_url,
                "preview_url": av.preview_url,
                "status": av.status
            }

    # 提取当前口播台词与商品
    orchestrator = ACTIVE_ORCHESTRATORS.get(live_sess.id)
    current_script = (
        orchestrator.script_queue[0] 
        if orchestrator and orchestrator.script_queue 
        else "哈喽各位宝贝们！欢迎来到我们的智能直播间，点击小黄车领专属优惠券哦！"
    )
    current_product = orchestrator.current_product if orchestrator else None

    return {
        "session_id": live_sess.id,
        "room_id": live_sess.room_id,
        "status": live_sess.status,
        "is_orchestrator_running": is_running,
        "rtmp_url": live_sess.rtmp_url,
        "http_flv_url": live_sess.http_flv_url,
        "viewer_count": live_sess.viewer_count,
        "peak_viewers": live_sess.peak_viewers,
        "started_at": live_sess.started_at,
        "avatar": avatar_data,
        "current_script": current_script,
        "current_product": current_product,
        "active_streaming_room": streaming_sess.room_id if (streaming_sess and streaming_sess.room_id != live_sess.room_id) else None,
        "active_session_id": streaming_sess.id if (streaming_sess and streaming_sess.id != live_sess.id) else None,
    }

@router.post("/danmaku")
async def send_danmaku(
    req: DanmakuSendReq,
    session: Session = Depends(get_session)
):
    # 敏感词审查与自动脱敏
    audit_res = audit_text_compliance(req.content)
    safe_content = audit_res["masked_text"]

    # 1. 持久化记录
    msg = LiveMessage(
        session_id=req.session_id,
        user_name=req.user_name or "观众",
        content=safe_content,
        message_type="danmaku"
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)

    # 2. 注入编排器优先级队列
    if req.session_id in ACTIVE_ORCHESTRATORS:
        await ACTIVE_ORCHESTRATORS[req.session_id].enqueue_danmaku(
            sender=msg.user_name,
            content=safe_content
        )

    # 3. 广播给前端 WebSocket 观众
    if req.session_id in WS_ROOM_CONNECTIONS:
        payload = {
            "type": "danmaku",
            "id": msg.id,
            "sender": msg.user_name,
            "content": safe_content,
            "masked": not audit_res["is_compliant"],
            "timestamp": datetime.utcnow().strftime("%H:%M:%S")
        }
        for ws in list(WS_ROOM_CONNECTIONS[req.session_id]):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    return {
        "status": "ok",
        "message_id": msg.id,
        "is_compliant": audit_res["is_compliant"],
        "violations": audit_res["violations"]
    }

@router.get("/messages", response_model=List[LiveMessage])
def list_messages(
    session_id: int = Query(...),
    limit: int = Query(50),
    session: Session = Depends(get_session)
):
    query = (
        select(LiveMessage)
        .where(LiveMessage.session_id == session_id)
        .order_by(LiveMessage.id.desc())
        .limit(limit)
    )
    results = session.exec(query).all()
    return list(reversed(results))

@router.post("/insert_script")
def insert_script(
    req: InsertScriptReq
):
    if req.session_id in ACTIVE_ORCHESTRATORS:
        audit_res = audit_text_compliance(req.content)
        safe_content = audit_res["masked_text"]
        ACTIVE_ORCHESTRATORS[req.session_id].add_script_chunk(safe_content, req.priority or True)
        return {
            "status": "ok",
            "message": "Script inserted into live orchestrator queue.",
            "is_compliant": audit_res["is_compliant"],
            "violations": audit_res["violations"]
        }
    raise HTTPException(status_code=400, detail=f"Live session {req.session_id} is not active")

@router.post("/switch_product")
def switch_product(
    req: SwitchProductReq,
    session: Session = Depends(get_session)
):
    prod = session.get(Product, req.product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {req.product_id} not found")

    if req.session_id in ACTIVE_ORCHESTRATORS:
        ACTIVE_ORCHESTRATORS[req.session_id].set_current_product({
            "id": prod.id,
            "title": prod.title,
            "price": prod.price,
            "original_price": prod.original_price,
            "selling_points": prod.selling_points_json
        })
        return {"status": "ok", "product_title": prod.title}
    raise HTTPException(status_code=400, detail=f"Live session {req.session_id} is not active")

# ----------------- WebSocket Live Interaction Channel -----------------

@router.websocket("/ws/{session_id}")
async def live_websocket_endpoint(websocket: WebSocket, session_id: int):
    await websocket.accept()
    if session_id not in WS_ROOM_CONNECTIONS:
        WS_ROOM_CONNECTIONS[session_id] = []
    WS_ROOM_CONNECTIONS[session_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": int(datetime.utcnow().timestamp())})
            elif msg_type == "danmaku":
                raw_content = data.get("content", "")
                sender = data.get("sender", "观众")
                audit_res = audit_text_compliance(raw_content)
                safe_content = audit_res["masked_text"]
                if session_id in ACTIVE_ORCHESTRATORS:
                    await ACTIVE_ORCHESTRATORS[session_id].enqueue_danmaku(sender, safe_content)
                payload = {
                    "type": "danmaku",
                    "sender": sender,
                    "content": safe_content,
                    "masked": not audit_res["is_compliant"],
                    "timestamp": datetime.utcnow().strftime("%H:%M:%S")
                }
                for ws in list(WS_ROOM_CONNECTIONS.get(session_id, [])):
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        pass
    finally:
        if session_id in WS_ROOM_CONNECTIONS and websocket in WS_ROOM_CONNECTIONS[session_id]:
            WS_ROOM_CONNECTIONS[session_id].remove(websocket)
