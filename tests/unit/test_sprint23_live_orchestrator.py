import os
import sys
import pytest
import asyncio
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from core.security import create_access_token
from services.live_orchestrator import LiveOrchestrator, SessionState

@pytest.mark.asyncio
async def test_live_orchestrator_lifecycle_and_queues():
    orch = LiveOrchestrator(
        session_id=999,
        room_id="room_orch_test",
        avatar_id=1,
        stream_key="stream_key_999"
    )
    assert orch.state == SessionState.IDLE
    assert orch.stream_key == "stream_key_999"

    # Start streaming
    await orch.start_streaming()
    assert orch.state == SessionState.STREAMING
    assert orch.is_running is True

    # Test enqueue danmaku
    await orch.enqueue_danmaku(sender="小李", content="这个耳机能降噪多少分贝？")
    assert orch.priority_danmaku_queue.qsize() == 1

    # Test switch product
    orch.set_current_product({"title": "智能耳机", "price": 199.0})
    assert orch.current_product["title"] == "智能耳机"

    # Let loop process a cycle
    await asyncio.sleep(0.3)

    # Stop streaming
    await orch.stop_streaming()
    assert orch.state == SessionState.FINISHED
    assert orch.is_running is False

def test_live_api_endpoints_flow():
    token = create_access_token(data={"sub": "admin_test", "role": "admin", "tenant_id": "corp_test"})
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        # 0. Create active compliant avatar for live test
        av_res = client.post(
            "/api/v1/avatars",
            json={
                "name": "直播编排合规主播",
                "avatar_type": "lingcast_live",
                "status": "active",
                "config_json": '{"licensing_status": "verified"}'
            },
            headers=headers
        )
        assert av_res.status_code == 201
        valid_avatar_id = av_res.json()["id"]

        # 1. Start live
        start_payload = {
            "title": "大促直播测试",
            "room_id": f"room_api_test_{valid_avatar_id}",
            "avatar_id": valid_avatar_id
        }
        start_res = client.post("/api/v1/live/start", json=start_payload, headers=headers)
        assert start_res.status_code == 201
        data = start_res.json()
        session_id = data["session_id"]
        assert data["session_status"] == "streaming"
        assert "stream_key" in data

        # 2. Get status
        status_res = client.get(f"/api/v1/live/status?session_id={session_id}", headers=headers)
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "streaming"

        # 3. Send danmaku
        danmaku_res = client.post("/api/v1/live/danmaku", json={
            "session_id": session_id,
            "user_name": "老粉小明",
            "content": "求问今天有什么优惠券？"
        }, headers=headers)
        assert danmaku_res.status_code == 200
        assert danmaku_res.json()["status"] == "ok"

        # 4. Read messages
        msg_res = client.get(f"/api/v1/live/messages?session_id={session_id}", headers=headers)
        assert msg_res.status_code == 200
        messages = msg_res.json()
        assert len(messages) >= 1
        assert any("优惠券" in m["content"] for m in messages)

        # 5. Insert emergency script
        script_res = client.post("/api/v1/live/insert_script", json={
            "session_id": session_id,
            "content": "突发福利！前10名加送数据线一条！",
            "priority": True
        }, headers=headers)
        assert script_res.status_code == 200

        # 6. Stop live
        stop_res = client.post("/api/v1/live/stop", json={"session_id": session_id}, headers=headers)
        assert stop_res.status_code == 200
        assert stop_res.json()["status"] == "ok"
