import os
from pathlib import Path
from typing import Any, Dict
import yaml

CONFIG_PATH = Path(os.getenv("SERVICES_CONFIG_PATH", Path(__file__).parent.parent.parent / "config" / "services.yaml"))

class AppConfig:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        env = os.getenv("APP_ENV", "development").lower()
        if not CONFIG_PATH.exists():
            self._config = {}
            return

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            all_configs = yaml.safe_load(f) or {}

        # Merge default with env specific
        default_cfg = all_configs.get("default", {})
        env_cfg = all_configs.get(env, {})
        merged = {**default_cfg, **env_cfg}

        # Override with active environment variables if present
        if os.getenv("REDIS_URL"):
            merged.setdefault("redis", {})["url"] = os.getenv("REDIS_URL")
        if os.getenv("TTS_SERVICE_URL"):
            merged.setdefault("tts", {})["service_url"] = os.getenv("TTS_SERVICE_URL")
        if os.getenv("RAG_SERVICE_URL"):
            merged.setdefault("rag", {})["service_url"] = os.getenv("RAG_SERVICE_URL")
        if os.getenv("SRS_RTMP_URL"):
            merged.setdefault("srs", {})["rtmp_base_url"] = os.getenv("SRS_RTMP_URL")
        if os.getenv("SRS_HTTP_URL"):
            merged.setdefault("srs", {})["http_flv_base_url"] = os.getenv("SRS_HTTP_URL")

        self._config = merged

    def get(self, section: str, default: Any = None) -> Any:
        return self._config.get(section, default)

    @property
    def raw(self) -> Dict[str, Any]:
        return self._config

config = AppConfig()
