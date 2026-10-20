import os
import re
import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
import requests

logger = logging.getLogger("LLMSalesAgent")

AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")
AGNES_BASE_URL = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")

PRIMARY_MODEL = "agnes-3.0-flash"
FALLBACK_MODEL = "agnes-2.5-flash"

SYSTEM_SALES_PROMPT_TEMPLATE = """你是一名专业、热情、亲和力极强的 AI 顶级带货主播【{anchor_name}】。
当前直播间正在热推的主打商品如下：
- 商品名称: {product_title}
- 当前直播特惠价: ¥{product_price} (原价: ¥{original_price})
- 核心卖点: {selling_points}

【背景知识库事实依据 (RAG)】:
{knowledge_context}

【主播互动原则】:
1. 语言口语化、接地气、富有感染力，多使用直播互动常用语（如“宝贝们”、“家人们”、“扣1上车”等），严禁生硬说教。
2. 回复观众提问时必须以【背景知识库事实依据】为准，严禁胡编乱造参数。
3. 严格遵守《广告法》合规要求，绝不使用“第一”、“顶级”、“绝无仅有”等违禁极限词。
4. 语言精炼，每次回复控制在 30~80 字以内，适合口播朗读。
"""

class LLMSalesAgent:
    def __init__(
        self,
        anchor_name: str = "小婉",
        model: str = PRIMARY_MODEL,
        rag_url: str = RAG_SERVICE_URL
    ):
        self.anchor_name = anchor_name
        self.model = model
        self.rag_url = rag_url

    async def fetch_knowledge_context(self, query: str, kb_id: str = "default_kb", tenant_id: str = "default") -> str:
        """从 RAG 知识库微服务检索相关切片"""
        try:
            payload = {
                "kb_id": kb_id,
                "tenant_id": tenant_id,
                "query": query,
                "top_k": 2,
                "min_score": 0.05
            }
            # 非阻塞请求微服务
            resp = await asyncio.to_thread(
                lambda: requests.post(f"{self.rag_url}/search", json=payload, timeout=3.0)
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return "\n".join([f"- {r['title']}: {r['content']}" for r in results])
        except Exception as e:
            logger.warning(f"RAG knowledge query skipped: {e}")
        return "暂无特定补充文档，请基于常识热情解答。"

    def split_into_speech_sentences(self, text: str) -> List[str]:
        """将完整段落切分为适合 TTS 朗读的短句，消灭多余符号"""
        cleaned = re.sub(r"[\*\#\-\(\)（）]", "", text)
        raw_sentences = re.split(r"([，。！？；\n\r]+)", cleaned)
        sentences = []
        buf = ""
        for part in raw_sentences:
            if not part:
                continue
            buf += part
            if re.search(r"[，。！？；\n\r]", part) and len(buf.strip()) >= 6:
                sentences.append(buf.strip())
                buf = ""
        if buf.strip():
            sentences.append(buf.strip())
        return sentences or [text.strip()]

    async def generate_reply(
        self,
        danmaku_text: str,
        sender_name: str,
        current_product: Optional[Dict[str, Any]] = None,
        kb_id: str = "default_kb",
        tenant_id: str = "default"
    ) -> str:
        """针对单条弹幕生成直播带货答复"""
        # 1. 抓取知识库
        knowledge_context = await self.fetch_knowledge_context(danmaku_text, kb_id, tenant_id)

        # 2. 组装 Prompt
        prod = current_product or {
            "title": "爆款热卖好物",
            "price": "99.0",
            "original_price": "199.0",
            "selling_points": "高品质保证，7天无理由退换货"
        }
        system_prompt = SYSTEM_SALES_PROMPT_TEMPLATE.format(
            anchor_name=self.anchor_name,
            product_title=prod.get("title", ""),
            product_price=prod.get("price", ""),
            original_price=prod.get("original_price", ""),
            selling_points=json.dumps(prod.get("selling_points", []), ensure_ascii=False),
            knowledge_context=knowledge_context
        )

        user_prompt = f"观众【{sender_name}】在弹幕中说: \"{danmaku_text}\"。请以主播口吻针对性回应TA并自然带出商品优势。"

        # 3. 调用大模型 (带官方 Fallback 容灾切换)
        for target_model in [self.model, FALLBACK_MODEL]:
            try:
                if not AGNES_API_KEY:
                    # Mock response for testing or offline environment
                    return f"感谢【{sender_name}】的提问！关于您问的“{danmaku_text}”，我们这款{prod.get('title')}绝对保真包邮，现货速发，放心拍！"

                headers = {
                    "Authorization": f"Bearer {AGNES_API_KEY}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
                resp = await asyncio.to_thread(
                    lambda: requests.post(f"{AGNES_BASE_URL}/chat/completions", headers=headers, json=body, timeout=8.0)
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"Model {target_model} returned {resp.status_code}, attempting fallback...")
            except Exception as e:
                logger.warning(f"Error calling {target_model}: {e}")

        # Final resilient fallback
        return f"感谢【{sender_name}】支持！这款{prod.get('title')}现在下单立享粉丝专属特惠，点击下方小黄车立即抢购！"
