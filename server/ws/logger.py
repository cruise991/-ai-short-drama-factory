import asyncio
import re
import datetime
from collections import deque
from typing import List
from fastapi import WebSocket

def sanitize_log(message: str) -> str:
    """Sanitize sensitive credentials from log streams."""
    if not isinstance(message, str):
        message = str(message)
    # Mask Bearer tokens
    message = re.sub(r'(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}', r'\1[REDACTED_SECRET]', message, flags=re.IGNORECASE)
    # Mask OpenAI-style keys
    message = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-[REDACTED_SECRET]', message, flags=re.IGNORECASE)
    # Mask api_key = "..."
    message = re.sub(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_\-]{15,}', r'\1[REDACTED_SECRET]', message, flags=re.IGNORECASE)
    return message


class ConnectionManager:
    def __init__(self, history_limit: int = 1000):
        self.active_connections: List[WebSocket] = []
        self.history: deque = deque(maxlen=history_limit)
        self._loop = None

    def _get_loop(self):
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
        return self._loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 1. If history is empty, seed with system ready message
        if not self.history:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ready_msg = f"[{now_str}] [System] AI Short Drama & Video Orchestrator Engine online. Real-time log stream ready."
            self.history.append(ready_msg)

        # 2. Replay all buffered history logs to this newly connected client
        for historical_msg in list(self.history):
            try:
                await websocket.send_text(historical_msg)
            except Exception:
                break

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        if not message:
            return
            
        clean_msg = sanitize_log(message)
        # Store in circular history buffer
        self.history.append(clean_msg)

        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(clean_msg)
            except Exception:
                disconnected.append(connection)
                
        for d in disconnected:
            self.disconnect(d)

    def broadcast_sync(self, message: str):
        """Thread-safe synchronous broadcast for worker loops and regular functions."""
        if not message:
            return
            
        loop = self._get_loop()
        clean_msg = sanitize_log(message)
        self.history.append(clean_msg)
        
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self._send_to_all(clean_msg), loop)

    async def _send_to_all(self, message: str):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for d in disconnected:
            self.disconnect(d)

manager = ConnectionManager()

