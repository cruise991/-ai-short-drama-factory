import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from services.live_renderer import LiveRenderEngine, FFmpegStreamer, RenderState
from services.llm_sales_agent import LLMSalesAgent
from services.tts_pipeline import TTSPipeline
from core.redis_bus import RedisMessageBus, STREAM_DANMAKU, STREAM_EVENTS
from core.compliance import audit_text_compliance
from core.watermark import WatermarkConfig

logger = logging.getLogger("LiveOrchestrator")

class SessionState(str, Enum):
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    FINISHED = "finished"

class LiveOrchestrator:
    """
    LingCast 智能直播核心编排控制器。
    负责维持直播间状态机、话术轮播、弹幕消费、插队问答和音画渲染管道调度。
    """
    def __init__(
        self,
        session_id: int,
        room_id: str,
        avatar_id: int,
        stream_key: str,
        redis_url: Optional[str] = None,
        srs_rtmp_base: str = "rtmp://localhost:1935/live",
        watermark_config: Optional[WatermarkConfig] = None
    ):
        self.session_id = session_id
        self.room_id = room_id
        self.avatar_id = avatar_id
        self.stream_key = stream_key
        self.state = SessionState.IDLE
        self.rtmp_url = f"{srs_rtmp_base}/{stream_key}"
        self.http_flv_url = f"http://localhost:8085/live/{stream_key}.flv"
        self.watermark_config = watermark_config or WatermarkConfig()

        # 依赖模块实例
        self.redis_bus = RedisMessageBus(redis_url)
        self.renderer = LiveRenderEngine(avatar_id=avatar_id, is_simulation=True)
        self.streamer = FFmpegStreamer(
            rtmp_target_url=self.rtmp_url,
            watermark_filter=self.watermark_config.build_ffmpeg_filter()
        )
        self.llm_agent = LLMSalesAgent(anchor_name="小婉")
        self.tts = TTSPipeline()

        # 直播内容与状态
        self.current_product: Optional[Dict[str, Any]] = None
        self.script_queue: List[str] = [
            "哈喽各位宝贝们！欢迎来到我们的智能直播间！",
            "今天给大家带来的是我们精选爆款好物，保真包邮！",
            "点击右下角小黄车即可领券立减，手慢无哦！"
        ]
        self.priority_danmaku_queue: asyncio.Queue = asyncio.Queue()
        self.loop_task: Optional[asyncio.Task] = None
        self.is_running = False

    def set_current_product(self, product: Dict[str, Any]):
        self.current_product = product
        logger.info(f"[Orchestrator] Active product updated: {product.get('title')}")

    def add_script_chunk(self, script_text: str, priority: bool = False):
        if priority:
            self.script_queue.insert(0, script_text)
        else:
            self.script_queue.append(script_text)

    async def enqueue_danmaku(self, sender: str, content: str):
        """接收并排队弹幕（自动执行敏感词合规审查与遮罩）"""
        audit_res = audit_text_compliance(content)
        safe_content = audit_res["masked_text"] if not audit_res["is_compliant"] else content
        if not audit_res["is_compliant"]:
            logger.warning(f"[Orchestrator] Danmaku from {sender} contained violations {audit_res['violations']}, masked: {safe_content}")
        await self.priority_danmaku_queue.put({"sender": sender, "content": safe_content})

    async def start_streaming(self):
        """启动直播流与编排主循环"""
        if self.state == SessionState.STREAMING:
            return
        logger.info(f"[Orchestrator] Starting live session #{self.session_id} in room [{self.room_id}]")
        self.state = SessionState.STREAMING
        self.is_running = True
        self.streamer.start(dry_run=True)

        # 启动常驻调度事件循环
        self.loop_task = asyncio.create_task(self._orchestrator_loop())

    async def stop_streaming(self):
        """停止直播并释放硬件与推流管道"""
        logger.info(f"[Orchestrator] Stopping live session #{self.session_id}")
        self.is_running = False
        self.state = SessionState.FINISHED
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
            self.loop_task = None
        self.streamer.stop()

    async def _orchestrator_loop(self):
        """
        核心编排主循环：
        1. 优先检查高优先级弹幕互动队列（Priority Queue）
        2. 若无观众弹幕，则执行背景话术轮播（Script Carousel）
        3. 文本合规脱敏审计 -> 触发 TTS 音频合成 -> 驱动渲染器进行口型同步推流
        """
        while self.is_running and self.state == SessionState.STREAMING:
            try:
                speech_text = None
                sender_name = None

                # 1. 检查弹幕互动队列
                if not self.priority_danmaku_queue.empty():
                    danmaku = await self.priority_danmaku_queue.get()
                    sender_name = danmaku["sender"]
                    content = danmaku["content"]
                    logger.info(f"[Orchestrator] Processing danmaku from {sender_name}: {content}")
                    speech_text = await self.llm_agent.generate_reply(
                        danmaku_text=content,
                        sender_name=sender_name,
                        current_product=self.current_product
                    )
                # 2. 无弹幕时轮播背景台本
                elif self.script_queue:
                    speech_text = self.script_queue.pop(0)
                    # 循环放回末尾保证持续有声音
                    self.script_queue.append(speech_text)

                if speech_text:
                    # 3. 广告法与敏感词合规脱敏
                    audit_res = audit_text_compliance(speech_text)
                    if not audit_res["is_compliant"]:
                        logger.warning(f"[Orchestrator] Speech contained non-compliant terms {audit_res['violations']}, applying mask.")
                        speech_text = audit_res["masked_text"]

                    # 4. 语音合成与渲染驱动
                    clip = await self.tts.synthesize(speech_text)
                    await self.renderer.render_speaking_chunk(clip.file_path, clip.duration_sec)
                else:
                    await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Orchestrator] Error in live loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)
