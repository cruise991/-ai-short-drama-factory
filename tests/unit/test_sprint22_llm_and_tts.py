import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from core.security import create_access_token
from services.llm_sales_agent import LLMSalesAgent
from services.tts_pipeline import TTSPipeline

@pytest.mark.asyncio
async def test_llm_sales_agent_speech_chunking_and_reply():
    agent = LLMSalesAgent(anchor_name="小婉测试")
    
    # 1. Test speech sentence chunking
    text = "家人们看过来！这款耳机支持主动混合降噪，续航长达40小时。今天直播间专属特惠只要299元，支持七天无理由退换货！"
    chunks = agent.split_into_speech_sentences(text)
    assert len(chunks) >= 2
    assert any("299" in c for c in chunks)

    # 2. Test reply generation
    reply = await agent.generate_reply(
        danmaku_text="降噪效果好不好？能不能连苹果手机？",
        sender_name="极客粉丝",
        current_product={"title": "旗舰降噪耳机 Pro", "price": "299", "original_price": "599", "selling_points": ["40dB降噪", "多设备兼容"]}
    )
    assert len(reply) > 10
    assert "极客粉丝" in reply or "降噪" in reply

@pytest.mark.asyncio
async def test_tts_pipeline_prefetch_and_caching():
    pipeline = TTSPipeline()
    sentences = ["欢迎来到直播间！", "今天的主推商品性价比非常高！"]
    
    # Prefetch batch
    clips = await pipeline.prefetch_queue(sentences, voice="zh-CN-XiaoxiaoNeural")
    assert len(clips) == 2
    assert clips[0].duration_sec > 0
    assert clips[1].duration_sec > 0

    # Test cache hit on identical sentence
    second_run = await pipeline.synthesize("欢迎来到直播间！", voice="zh-CN-XiaoxiaoNeural")
    assert second_run.duration_sec == clips[0].duration_sec

def test_product_and_knowledge_api_crud():
    token = create_access_token(data={"sub": "admin_test", "role": "admin", "tenant_id": "corp_test"})
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        # 1. Create product
        prod_payload = {
            "title": "无线静音鼠标",
            "tenant_id": "corp_test",
            "price": 79.0,
            "original_price": 149.0,
            "sku": "MOUSE-01",
            "selling_points": ["静音微动", "三模连接", "轻量化设计"]
        }
        p_res = client.post("/api/v1/products", json=prod_payload, headers=headers)
        assert p_res.status_code == 201
        prod_id = p_res.json()["id"]

        # 2. Query product list
        p_list = client.get("/api/products?tenant_id=corp_test", headers=headers)
        assert p_list.status_code == 200
        assert any(p["id"] == prod_id for p in p_list.json())

        # 3. Create knowledge base
        kb_payload = {
            "name": "3C数码直播知识库",
            "tenant_id": "corp_test",
            "chunk_size": 256
        }
        kb_res = client.post("/api/v1/knowledge", json=kb_payload, headers=headers)
        assert kb_res.status_code == 201
        kb_id = kb_res.json()["id"]

        # 4. Add document
        doc_payload = {
            "title": "无线鼠标质保政策",
            "doc_id": "mouse_policy",
            "content": "本款无线静音鼠标质保两年，出现非人为故障直接免费换新，全国顺丰包邮发货。"
        }
        d_res = client.post(f"/api/v1/knowledge/{kb_id}/documents", json=doc_payload, headers=headers)
        assert d_res.status_code == 201
        assert d_res.json()["doc_id"] == "mouse_policy"

        # 5. Test search
        s_res = client.post(f"/api/v1/knowledge/{kb_id}/search", json={"query": "鼠标坏了保修吗", "top_k": 1}, headers=headers)
        assert s_res.status_code == 200
        results = s_res.json()["results"]
        assert len(results) > 0
