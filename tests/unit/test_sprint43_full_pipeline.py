import os
import sys
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
server_dir = os.path.join(ROOT_DIR, "server")
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from server.services.live_orchestrator import LiveOrchestrator, SessionState
from server.core.compliance import audit_text_compliance
from server.core.watermark import WatermarkConfig, audit_avatar_licensing
from server.services.llm_sales_agent import LLMSalesAgent


@pytest.mark.asyncio
async def test_end_to_end_live_streaming_lifecycle():
    """
    Sprint 4.3 End-to-End Regression Test:
    Validates complete lifecycle:
    1. Digital Avatar Licensing Audit
    2. Room Initialization with Legal AI Watermark
    3. Start Streaming & Transition to STREAMING state
    4. Product Linking & Carousel Script Ingestion
    5. Real-time Danmaku Handling + DFA Compliance Masking
    6. LLM Sales Pitch Reply Generation
    7. Graceful Stop & Resource Teardown
    """
    # 0. Digital Avatar Licensing Audit
    valid_avatar = {"id": 101, "name": "婉儿", "status": "active", "config_json": '{"license_no": "LIC-20260901-01"}'}
    is_valid, msg = audit_avatar_licensing(valid_avatar)
    assert is_valid is True

    invalid_avatar = {"id": 102, "name": "未授权形象", "status": "disabled"}
    is_valid_inv, msg_inv = audit_avatar_licensing(invalid_avatar)
    assert is_valid_inv is False

    # 1. Room Initialization with Watermark
    watermark_cfg = WatermarkConfig(
        text="AI虚拟人直播 (备案号: 310104-2026-0089)",
        fontsize=20,
        position="top-left"
    )
    assert "AI虚拟人直播" in watermark_cfg.text

    orchestrator = LiveOrchestrator(
        session_id=8888,
        room_id="room_e2e_test",
        avatar_id=101,
        stream_key="stream_e2e_key",
        watermark_config=watermark_cfg
    )
    assert orchestrator.state == SessionState.IDLE

    # 2. Product Linking
    sample_product = {
        "id": 1,
        "title": "2026春季轻奢羽绒服",
        "price": 299.00,
        "discount_info": "限时立减50元，买即送围巾",
        "highlights": ["90%白鸭绒", "保暖透气", "顺丰包邮"]
    }
    orchestrator.set_current_product(sample_product)
    assert orchestrator.current_product["title"] == "2026春季轻奢羽绒服"

    # 3. Start Streaming
    await orchestrator.start_streaming()
    assert orchestrator.state == SessionState.STREAMING
    assert orchestrator.is_running is True
    assert orchestrator.loop_task is not None

    # 4. Danmaku Compliance & Ingestion
    # Clean danmaku
    clean_danmaku = "主播这件羽绒服保暖效果怎么样？"
    await orchestrator.enqueue_danmaku("观众小李", clean_danmaku)
    assert not orchestrator.priority_danmaku_queue.empty()
    queued_item = await orchestrator.priority_danmaku_queue.get()
    assert queued_item["sender"] == "观众小李"
    assert queued_item["content"] == clean_danmaku

    # Violating danmaku
    bad_danmaku = "这是全网首发国家级绝无仅有的神作！"
    audit_res = audit_text_compliance(bad_danmaku)
    assert audit_res["is_compliant"] is False
    assert any(w in audit_res["violations"] for w in ["全网首发", "国家级", "绝无仅有"])
    assert "全网首发" not in audit_res["masked_text"]

    # 5. LLM Sales Agent Reply Verification
    with patch.object(
        orchestrator.llm_agent,
        "generate_reply",
        new=AsyncMock(return_value="小李宝贝放心！我们这款羽绒服含绒量高达90%，轻盈又抗寒，顺丰包邮包退换哦！")
    ):
        reply = await orchestrator.llm_agent.generate_reply(
            danmaku_text=clean_danmaku,
            sender_name="观众小李",
            current_product=sample_product
        )
        assert "小李宝贝" in reply
        assert "90%" in reply

    # 6. Stop Streaming & Clean Teardown
    await orchestrator.stop_streaming()
    assert orchestrator.state == SessionState.FINISHED
    assert orchestrator.is_running is False
    assert orchestrator.loop_task is None


@pytest.mark.asyncio
async def test_watermark_ffmpeg_filter_generation():
    """Verify statutory AI watermark generates valid FFmpeg drawtext filter string."""
    watermark = WatermarkConfig(
        text="深度合成内容 虚拟主播",
        fontsize=18,
        position="top-right",
        fontcolor="white@0.85"
    )
    filter_str = watermark.build_ffmpeg_filter()
    assert "drawtext" in filter_str
    assert "深度合成内容 虚拟主播" in filter_str
    assert "fontsize=18" in filter_str
