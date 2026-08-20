"""
API connectivity test script (urllib variant).
Usage: python test_api2.py
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

    req = urllib.request.Request("https://apihub.agnes-ai.com/v1/chat/completions", method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    payload = json.dumps({
        "model": "agnes-2.0-flash",
        "messages": [{"role": "user", "content": "hello"}]
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=payload, timeout=10) as response:
            print("STATUS", response.status)
            print("CONTENT", response.read().decode("utf-8"))
    except Exception as e:
        print("ERROR", e)
