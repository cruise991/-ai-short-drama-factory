import os

def load_env(filepath=None):
    if not filepath:
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        
    config = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
    return config

def get_config(key, default=None):
    """Utility to load from .env and fallback to os.environ or default"""
    env_config = load_env()
    return env_config.get(key, os.environ.get(key, default))
