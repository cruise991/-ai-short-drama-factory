import os
import sys
import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from models.database import get_session, Avatar, AvatarStatus
from core.security import create_access_token
from core.compliance import DFASensitiveFilter, audit_text_compliance
from core.watermark import WatermarkConfig, audit_avatar_licensing
from services.live_renderer import FFmpegStreamer

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "compliance_tester", "tenant_id": "tenant_test"})
    return {"Authorization": f"Bearer {token}"}

def test_dfa_sensitive_filter_and_audit():
    custom_filter = DFASensitiveFilter(["特价第一", "赌博"])
    
    clean_text = "今天我们的西服套装剪裁非常修身，质感上乘。"
    assert custom_filter.is_clean(clean_text)[0] is True
    assert custom_filter.mask(clean_text) == clean_text

    dirty_text = "我们是特价第一的店铺，拒绝任何赌博行为！"
    is_clean, violations = custom_filter.is_clean(dirty_text)
    assert is_clean is False
    assert set(violations) == {"特价第一", "赌博"}
    
    masked = custom_filter.mask(dirty_text)
    assert "****" in masked
    assert "**" in masked
    assert "特价第一" not in masked
    assert "赌博" not in masked

    # 验证系统内置违禁词库
    audit_res = audit_text_compliance("本产品独家首创，包治百病，买到就是赚到！")
    assert audit_res["is_compliant"] is False
    assert "独家首创" in audit_res["violations"]
    assert "包治百病" in audit_res["violations"]
    assert "独家首创" not in audit_res["masked_text"]
    assert "包治百病" not in audit_res["masked_text"]

def test_watermark_config_and_ffmpeg_streamer():
    wm = WatermarkConfig(text="AI合成主播 · 请理性消费", position="top-right")
    filter_str = wm.build_ffmpeg_filter()
    assert "drawtext=text='AI合成主播 · 请理性消费'" in filter_str
    assert "x=w-tw-24:y=24" in filter_str

    wm_left = WatermarkConfig(position="top-left")
    assert "x=24:y=24" in wm_left.build_ffmpeg_filter()

    # 验证推流管道命令注入
    streamer = FFmpegStreamer(
        rtmp_target_url="rtmp://localhost:1935/live/test_stream",
        watermark_filter=filter_str
    )
    cmd = streamer.build_ffmpeg_cmd()
    assert "-vf" in cmd
    vf_index = cmd.index("-vf")
    assert cmd[vf_index + 1] == filter_str

def test_avatar_licensing_audit():
    # 1. 空形象
    valid, reason = audit_avatar_licensing(None)
    assert valid is False

    # 2. 状态异常 (archived / training)
    valid, reason = audit_avatar_licensing({"status": "archived"})
    assert valid is False
    assert "归档停用" in reason

    valid, reason = audit_avatar_licensing({"status": "training"})
    assert valid is False
    assert "待审核或训练状态" in reason

    # 3. 授权异常
    valid, reason = audit_avatar_licensing({
        "status": "active",
        "config_json": json.dumps({"licensing_status": "revoked"})
    })
    assert valid is False
    assert "异常" in reason

    # 4. 正常授权
    valid, reason = audit_avatar_licensing({
        "status": "active",
        "config_json": json.dumps({"licensing_status": "verified"})
    })
    assert valid is True

def test_live_api_compliance_and_licensing_integration(auth_headers):
    # 1. 准备测试数据：一个归档的数字人和一个正常的数字人
    resp_archived = client.post(
        "/api/v1/avatars",
        json={
            "name": "已归档未授权主播",
            "avatar_type": "lingcast_live",
            "status": "archived"
        },
        headers=auth_headers
    )
    assert resp_archived.status_code == 201
    archived_avatar_id = resp_archived.json()["id"]

    resp_active = client.post(
        "/api/v1/avatars",
        json={
            "name": "合规签约授权主播",
            "avatar_type": "lingcast_live",
            "status": "active",
            "config_json": json.dumps({"licensing_status": "verified"})
        },
        headers=auth_headers
    )
    assert resp_active.status_code == 201
    active_avatar_id = resp_active.json()["id"]

    # 2. 尝试使用未授权数字人开播 -> 应被 400 拦截
    fail_start = client.post(
        "/api/v1/live/start",
        json={
            "title": "违规开播测试",
            "room_id": f"room_fail_{archived_avatar_id}",
            "avatar_id": archived_avatar_id
        },
        headers=auth_headers
    )
    assert fail_start.status_code == 400
    assert "数字人肖像授权合规审查未通过" in fail_start.json()["detail"]

    # 3. 使用合规授权数字人开播 -> 成功
    success_start = client.post(
        "/api/v1/live/start",
        json={
            "title": "合规开播测试",
            "room_id": f"room_success_{active_avatar_id}",
            "avatar_id": active_avatar_id
        },
        headers=auth_headers
    )
    assert success_start.status_code == 201
    session_id = success_start.json()["session_id"]

    # 4. 发送违规弹幕 -> 验证自动脱敏
    danmaku_resp = client.post(
        "/api/v1/live/danmaku",
        json={
            "session_id": session_id,
            "user_name": "热心观众小明",
            "content": "主播你家是全网第一吗？有没有洗钱啊？"
        },
        headers=auth_headers
    )
    assert danmaku_resp.status_code == 200
    res_data = danmaku_resp.json()
    assert res_data["is_compliant"] is False
    assert "全网第一" in res_data["violations"] or "洗钱" in res_data["violations"]

    # 查询弹幕记录，确认数据库中存储的是脱敏文本
    msg_list = client.get(
        f"/api/v1/live/messages?session_id={session_id}",
        headers=auth_headers
    )
    assert msg_list.status_code == 200
    stored_msgs = msg_list.json()
    latest_msg = stored_msgs[-1]
    assert "全网第一" not in latest_msg["content"]
    assert "****" in latest_msg["content"] or "**" in latest_msg["content"]

    # 5. 停播并释放
    client.post("/api/v1/live/stop", json={"session_id": session_id}, headers=auth_headers)
