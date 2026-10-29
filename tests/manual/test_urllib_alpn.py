import urllib.request
import json
import ssl
import sys
import os

if __name__ == "__main__":
    url = "https://apihub.agnes-ai.com/v1/models"
    ctx = ssl.create_default_context()
    if os.environ.get("SKIP_TLS_VERIFY"):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
    if hasattr(ctx, 'set_alpn_protocols'):
        ctx.set_alpn_protocols(['http/1.1'])

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print(response.read().decode('utf-8')[:100])
    except Exception as e:
        print("Error:", e)
