import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from services.live_renderer import LiveRenderEngine, RenderState, FFmpegStreamer

@pytest.mark.asyncio
async def test_live_render_engine_lifecycle():
    engine = LiveRenderEngine(avatar_id=101, is_simulation=True)
    assert engine.state == RenderState.IDLE
    assert engine.frames_rendered == 0

    # Test scene switching
    engine.switch_scene(scene_id=1, scene_video_url="https://cdn.example.com/bg1.mp4")
    assert engine.current_scene_id == 1
    assert engine.state == RenderState.IDLE

    # Test speech rendering
    result = await engine.render_speaking_chunk(audio_wav_path="/tmp/fake.wav", duration_sec=2.0)
    assert result["status"] == "success"
    assert result["frames"] == 50 # 2s * 25fps
    assert engine.frames_rendered == 50
    assert engine.state == RenderState.IDLE

def test_ffmpeg_streamer_pipeline():
    streamer = FFmpegStreamer(rtmp_target_url="rtmp://localhost:1935/live/test_room", fps=25)
    cmd = streamer.build_ffmpeg_cmd()
    assert "ffmpeg" in cmd
    assert "rtmp://localhost:1935/live/test_room" in cmd
    assert "libx264" in cmd
    assert "aac" in cmd

    # Test dry run start & stop
    streamer.start(dry_run=True)
    assert streamer.is_running is True
    streamer.stop()
    assert streamer.is_running is False

from core.security import create_access_token

def test_avatar_and_scene_api_crud():
    token = create_access_token(data={"sub": "admin_test", "role": "admin", "tenant_id": "corp_test"})
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        # 1. Create avatar via v1
        create_payload = {
            "name": "AI主播小婉",
            "tenant_id": "corp_test",
            "avatar_type": "lingcast_live",
            "voice_id": "zh-CN-XiaoxiaoNeural",
            "config_json": '{"pitch": "+2Hz"}'
        }
        res = client.post("/api/v1/avatars", json=create_payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        avatar_id = data["id"]
        assert data["name"] == "AI主播小婉"
        assert data["status"] == "active"

        # 2. Query list via legacy forward-compatible route (/api/avatars)
        list_res = client.get("/api/avatars?tenant_id=corp_test", headers=headers)
        assert list_res.status_code == 200
        avatars = list_res.json()
        assert any(a["id"] == avatar_id for a in avatars)

        # 3. Update avatar
        update_res = client.put(f"/api/v1/avatars/{avatar_id}", json={"name": "小婉-升级版"}, headers=headers)
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "小婉-升级版"

        # 4. Create scene
        scene_payload = {
            "title": "3C数码科技背景",
            "tenant_id": "corp_test",
            "video_url": "https://cdn.example.com/scenes/tech_studio.mp4",
            "duration": 45.0
        }
        scene_res = client.post("/api/v1/avatars/scenes/create", json=scene_payload, headers=headers)
        assert scene_res.status_code == 201
        assert scene_res.json()["title"] == "3C数码科技背景"

        # 5. Archive avatar
        del_res = client.delete(f"/api/v1/avatars/{avatar_id}", headers=headers)
        assert del_res.status_code == 200
        get_res = client.get(f"/api/v1/avatars/{avatar_id}", headers=headers)
        assert get_res.json()["status"] == "archived"
