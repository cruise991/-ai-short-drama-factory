import os
import json
import logging
from typing import Dict, Any, List, Optional
import redis

logger = logging.getLogger("RedisBus")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 核心消息流拓扑定义
STREAM_DANMAKU = "live:danmaku:{session_id}"       # 观众弹幕入站
STREAM_LLM_QUEUE = "live:llm_queue:{session_id}"   # LLM 编排与剧本/回复处理队列
STREAM_TTS_QUEUE = "live:tts_queue:{session_id}"   # TTS 语音合成任务队列
STREAM_RENDER_QUEUE = "live:render_queue:{session_id}" # 视频/Wav2Lip/LingCast 推理渲染队列
STREAM_EVENTS = "live:events:{session_id}"         # 直播状态机与系统广播事件 (推流/断流/商品切换)

# 消费者组命名定义
GROUP_DANMAKU_PROCESSOR = "cg_danmaku"
GROUP_LLM_WORKER = "cg_llm"
GROUP_TTS_WORKER = "cg_tts"
GROUP_RENDER_WORKER = "cg_render"


class RedisMessageBus:
    def __init__(self, redis_url: Optional[str] = None):
        self.url = redis_url or REDIS_URL
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False

    def publish_stream(self, stream_key: str, payload: Dict[str, Any]) -> str:
        """
        向指定的 Redis Stream 发布消息 (XADD)。
        自动将 dict 数据转换为字符串字段以便安全序列化。
        """
        flattened: Dict[str, str] = {}
        for k, v in payload.items():
            if isinstance(v, (dict, list)):
                flattened[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                flattened[k] = ""
            else:
                flattened[k] = str(v)

        msg_id = self.client.xadd(stream_key, flattened)
        return msg_id

    def create_group_safe(self, stream_key: str, group_name: str) -> bool:
        """
        安全创建消费者组 (XGROUP CREATE)。若已存在则忽略异常。
        """
        try:
            self.client.xgroup_create(name=stream_key, groupname=group_name, id="0", mkstream=True)
            return True
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                return True
            logger.error(f"创建消费者组失败 [{stream_key} -> {group_name}]: {e}")
            return False

    def read_stream_group(
        self,
        stream_key: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block_ms: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        通过消费者组读取消息 (XREADGROUP)。
        返回解析后的消息列表: [{"id": msg_id, "data": {...}}, ...]
        """
        try:
            entries = self.client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_key: ">"},
                count=count,
                block=block_ms
            )
            result = []
            if entries:
                for stream, msg_list in entries:
                    for msg_id, raw_fields in msg_list:
                        # 尝试反序列化 JSON 字段
                        parsed_fields = {}
                        for k, v in raw_fields.items():
                            try:
                                parsed_fields[k] = json.loads(v)
                            except (ValueError, TypeError):
                                parsed_fields[k] = v
                        result.append({"id": msg_id, "data": parsed_fields})
            return result
        except Exception as e:
            logger.error(f"读取 Stream 失败 [{stream_key}]: {e}")
            return []

    def ack_message(self, stream_key: str, group_name: str, msg_id: str) -> int:
        """
        确认消息已处理 (XACK)。
        """
        return self.client.xack(stream_key, group_name, msg_id)


# 全局默认单例
redis_bus = RedisMessageBus()
