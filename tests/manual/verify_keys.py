import os
import sys
import subprocess
import json
import ssl
import socket
from urllib.parse import urlparse

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from shared_tools.config_loader import get_config
    
    # Load keys dynamically from config or environment
    keys = []
    for i in range(1, 10):
        key = get_config(f"AGNES_API_KEY_{i}", "")
        if key:
            keys.append(key)
            
    if not keys:
        print("ERROR: No API keys found in .env or environment variables.")
        sys.exit(1)

    endpoint = "https://apihub.agnes-ai.com/v1/chat/completions"
    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = 443

    try:
        ip = socket.gethostbyname(host)
        resolve_arg = f"{host}:{port}:{ip}"
    except:
        resolve_arg = None

    payload = json.dumps({"model": "agnes-3.0-flash", "messages": [{"role": "user", "content": "hi"}]})

    for i, key in enumerate(keys):
        cmd = ["curl", "-s", "-k", "--http1.1", "-X", "POST", endpoint,
               "-H", "Content-Type: application/json",
               "-H", f"Authorization: Bearer {key}",
               "-d", payload,
               "--max-time", "10"]
        if resolve_arg:
            cmd.extend(["--resolve", resolve_arg])
            
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"KEY_{i+1}: CURL FAILED: {proc.stderr}")
        else:
            try:
                data = json.loads(proc.stdout)
                if "error" in data:
                    print(f"KEY_{i+1}: API ERROR - {data['error']}")
                else:
                    print(f"KEY_{i+1}: VALID!")
            except Exception as e:
                print(f"KEY_{i+1}: JSON ERROR - {proc.stdout}")
