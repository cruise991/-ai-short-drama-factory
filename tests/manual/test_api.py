"""
API connectivity test script.
Usage: python test_api.py
Requires AGNES_API_KEY_1 in .env or environment.
"""
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from shared_tools.config_loader import get_config

    api_key = get_config("AGNES_API_KEY_1", "")
    if not api_key:
        print("ERROR: AGNES_API_KEY_1 not set in .env or environment.")
        sys.exit(1)

    import urllib.request
    import json

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "agnes-2.0-flash",
        "messages": [{"role": "user", "content": "hello"}]
    }
    try:
        import requests
        res = requests.post(
            "https://apihub.agnes-ai.com/v1/chat/completions",
            headers=headers, json=payload, timeout=10
        )
        print("STATUS", res.status_code)
        print("CONTENT", res.text)
    except Exception as e:
        print("ERROR", e)
