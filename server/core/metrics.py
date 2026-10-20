import time
from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

class MetricsRegistry:
    def __init__(self):
        self.request_count: Dict[str, int] = {}
        self.request_durations: Dict[str, float] = {}
        self.active_streams: int = 0
        self.danmaku_processed_total: int = 0
        self.tts_requests_total: int = 0
        self.rag_requests_total: int = 0

    def inc_request(self, method: str, path_template: str, status_code: int):
        key = f'{method}_{path_template}_{status_code}'
        self.request_count[key] = self.request_count.get(key, 0) + 1

    def observe_duration(self, method: str, path_template: str, duration_sec: float):
        key = f'{method}_{path_template}'
        self.request_durations[key] = duration_sec

    def set_active_streams(self, count: int):
        self.active_streams = count

    def inc_danmaku(self, count: int = 1):
        self.danmaku_processed_total += count

    def inc_tts(self, count: int = 1):
        self.tts_requests_total += count

    def inc_rag(self, count: int = 1):
        self.rag_requests_total += count

    def to_prometheus_format(self) -> str:
        lines = [
            "# HELP shortdrama_http_requests_total Total number of HTTP requests processed",
            "# TYPE shortdrama_http_requests_total counter"
        ]
        for key, count in self.request_count.items():
            parts = key.split("_")
            method = parts[0]
            status = parts[-1]
            path = "_".join(parts[1:-1])
            lines.append(f'shortdrama_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

        lines.extend([
            "",
            "# HELP shortdrama_active_live_streams Current number of active live streams",
            "# TYPE shortdrama_active_live_streams gauge",
            f"shortdrama_active_live_streams {self.active_streams}",
            "",
            "# HELP shortdrama_danmaku_processed_total Total danmaku messages processed",
            "# TYPE shortdrama_danmaku_processed_total counter",
            f"shortdrama_danmaku_processed_total {self.danmaku_processed_total}",
            "",
            "# HELP shortdrama_tts_synthesis_total Total TTS requests triggered",
            "# TYPE shortdrama_tts_synthesis_total counter",
            f"shortdrama_tts_synthesis_total {self.tts_requests_total}",
            "",
            "# HELP shortdrama_rag_queries_total Total RAG search queries executed",
            "# TYPE shortdrama_rag_queries_total counter",
            f"shortdrama_rag_queries_total {self.rag_requests_total}"
        ])
        return "\n".join(lines) + "\n"

metrics = MetricsRegistry()

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return PlainTextResponse(metrics.to_prometheus_format(), media_type="text/plain; version=0.0.4")

        start = time.time()
        response: Response = await call_next(request)
        duration = time.time() - start

        path_label = request.url.path
        # Normalize IDs in paths for metric grouping
        if "/api/v1/" in path_label or "/api/" in path_label:
            parts = path_label.split("/")
            path_label = "/".join([p if not p.isdigit() else ":id" for p in parts])

        metrics.inc_request(request.method, path_label, response.status_code)
        metrics.observe_duration(request.method, path_label, duration)
        return response
