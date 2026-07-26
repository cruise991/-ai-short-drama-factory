from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.logger import manager

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't really expect the client to send anything, 
            # but we need to keep the connection open and listen for disconnects
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
