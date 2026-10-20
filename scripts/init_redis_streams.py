#!/usr/bin/env python3
"""
初始化 Redis Streams 消息总线拓扑
根据会话 ID 预置 5 条管道流与对应消费者组
"""

import os
import sys
import argparse
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    GROUP_DANMAKU_PROCESSOR,
    GROUP_LLM_WORKER,
    GROUP_TTS_WORKER,
    GROUP_RENDER_WORKER
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InitRedisStreams")


def init_streams(redis_url: str, session_id: str = "default_live_session") -> bool:
    bus = RedisMessageBus(redis_url)
    if not bus.ping():
        logger.warning(f"无法连接到 Redis ({redis_url})，若在无 Redis 纯本地环境运行则仅验证拓扑定义。")
        return False

    streams_and_groups = [
        (STREAM_DANMAKU.format(session_id=session_id), GROUP_DANMAKU_PROCESSOR),
        (STREAM_LLM_QUEUE.format(session_id=session_id), GROUP_LLM_WORKER),
        (STREAM_TTS_QUEUE.format(session_id=session_id), GROUP_TTS_WORKER),
        (STREAM_RENDER_QUEUE.format(session_id=session_id), GROUP_RENDER_WORKER),
        (STREAM_EVENTS.format(session_id=session_id), "cg_events"),
    ]

    logger.info(f"正在为直播会话 [{session_id}] 创建 Redis Streams 拓扑...")
    success = True
    for stream_key, group_name in streams_and_groups:
        ok = bus.create_group_safe(stream_key, group_name)
        if ok:
            logger.info(f"✅ Stream [{stream_key}] -> 消费者组 [{group_name}] 注册成功")
        else:
            logger.error(f"❌ Stream [{stream_key}] -> 消费者组 [{group_name}] 注册失败")
            success = False

    # 发送初始化系统事件
    event_stream = STREAM_EVENTS.format(session_id=session_id)
    msg_id = bus.publish_stream(event_stream, {
        "event_type": "SESSION_INITIALIZED",
        "session_id": session_id,
        "message": "Redis Streams pipeline initialized successfully"
    })
    logger.info(f"📢 初始化广播事件已发送: Stream [{event_stream}], Msg ID: {msg_id}")
    return success


def main():
    parser = argparse.ArgumentParser(description="Redis Streams 拓扑结构初始化工具")
    parser.add_argument("--url", default=os.getenv("REDIS_URL", "redis://localhost:6379/0"), help="Redis 连接 URL")
    parser.add_argument("--session-id", default="default_session", help="直播会话标识")
    args = parser.parse_args()

    init_streams(args.url, args.session_id)


if __name__ == "__main__":
    main()
