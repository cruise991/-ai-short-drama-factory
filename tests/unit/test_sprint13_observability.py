import os
import sys
import json
import logging
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from core.config_loader import config
from core.logging import JSONFormatter
from core.metrics import metrics

def test_config_loader_resolution():
    srs_cfg = config.get("srs")
    assert srs_cfg is not None
    assert srs_cfg["rtmp_port"] == 1935
    assert srs_cfg["http_flv_port"] == 8085

    tts_cfg = config.get("tts")
    assert tts_cfg is not None
    assert tts_cfg["default_voice"] == "zh-CN-XiaoxiaoNeural"

    rag_cfg = config.get("rag")
    assert rag_cfg is not None
    assert rag_cfg["chunk_size"] == 512

def test_json_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User login successful",
        args=(),
        exc_info=None
    )
    record.request_id = "req_test_12345"
    record.tenant_id = "corp_default"

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["level"] == "INFO"
    assert data["message"] == "User login successful"
    assert data["request_id"] == "req_test_12345"
    assert data["tenant_id"] == "corp_default"
    assert "timestamp" in data

def test_prometheus_metrics_and_request_id():
    with TestClient(app) as client:
        # Trigger a request
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

        # Test /metrics endpoint
        metrics_resp = client.get("/metrics")
        assert metrics_resp.status_code == 200
        assert metrics_resp.headers["content-type"].startswith("text/plain")
        content = metrics_resp.text
        assert "shortdrama_http_requests_total" in content
        assert "shortdrama_active_live_streams" in content
        assert "shortdrama_danmaku_processed_total" in content
