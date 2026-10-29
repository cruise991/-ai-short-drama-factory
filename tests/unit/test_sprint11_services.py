import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# 1. Test RAG Service
from services.rag.main import app as rag_app, KBStore, DocumentItem

def test_rag_health():
    client = TestClient(rag_app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rag"

def test_rag_index_and_search(tmp_path):
    # Use isolated storage path
    with patch("services.rag.main.STORAGE_DIR", tmp_path):
        client = TestClient(rag_app)
        
        # Index document
        payload = {
            "kb_id": "test_product_kb",
            "tenant_id": "tenant_001",
            "documents": [
                {
                    "doc_id": "p1",
                    "title": "智能降噪耳机说明",
                    "content": "这款智能降噪耳机具备40小时超长续航，支持三档主动混合降噪，采用全向四麦克风阵列，通话极其清晰，现货包邮。"
                },
                {
                    "doc_id": "p2",
                    "title": "速干运动T恤材质",
                    "content": "纯棉透气速干运动T恤，采用吸湿排汗高弹纤维织造，夏季运动首选，不起球不褪色，七天无理由退换货。"
                }
            ],
            "chunk_size": 100,
            "chunk_overlap": 20
        }
        resp = client.post("/index", json=payload)
        assert resp.status_code == 201
        res_data = resp.json()
        assert res_data["status"] == "ok"
        assert res_data["total_chunks"] >= 2
        
        # Search relevant query
        search_req = {
            "kb_id": "test_product_kb",
            "tenant_id": "tenant_001",
            "query": "耳机降噪和续航怎么样",
            "top_k": 2
        }
        s_resp = client.post("/search", json=search_req)
        assert s_resp.status_code == 200
        s_data = s_resp.json()
        assert len(s_data["results"]) > 0
        top_result = s_data["results"][0]
        assert top_result["doc_id"] == "p1"
        assert "降噪" in top_result["content"]
        assert top_result["score"] > 0
        
        # Delete KB
        del_resp = client.delete("/index/test_product_kb?tenant_id=tenant_001")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

# 2. Test TTS Service
from services.tts.main import app as tts_app

def test_tts_health():
    client = TestClient(tts_app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "tts"

def test_tts_voices_list():
    client = TestClient(tts_app)
    response = client.get("/voices")
    assert response.status_code == 200
    voices = response.json()
    assert len(voices) >= 4
    voice_ids = [v["voice_id"] for v in voices]
    assert "zh-CN-YunxiNeural" in voice_ids
    assert "en-US-JennyNeural" in voice_ids

# 3. Test Redis Bus Wrapper
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from core.redis_bus import (
    RedisMessageBus,
    STREAM_DANMAKU,
    STREAM_LLM_QUEUE,
    STREAM_TTS_QUEUE,
    STREAM_RENDER_QUEUE,
    STREAM_EVENTS,
    GROUP_DANMAKU_PROCESSOR
)

def test_redis_bus_initialization():
    bus = RedisMessageBus("redis://localhost:6379/0")
    assert bus.url == "redis://localhost:6379/0"
    assert "live:danmaku" in STREAM_DANMAKU
    assert "live:tts_queue" in STREAM_TTS_QUEUE
    assert GROUP_DANMAKU_PROCESSOR == "cg_danmaku"
