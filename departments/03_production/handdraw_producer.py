"""
Handdraw Video Production Module (Industrialized Pipeline)
==========================================================
Inspired by the Dance Video production logic:
1. Global Style Anchor Locking (Prompt Prefix Enforcement)
2. Multi-API Key Pooling & Auto-Failover (shared_tools.api_pool)
3. Strict Agnes Image 2.5 Flash API Schema Compliance
4. Decoupled Audio & Visual Workflows with Stage Caching
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared_tools.api_pool import get_agnes_keys, get_available_key, record_429
from shared_tools.config_loader import get_config

# Global Handdraw Style Anchor - Strictly Enforced on Every Shot
HANDDRAW_STYLE_ANCHOR = (
    "High quality modern editorial whiteboard cartoon illustration, "
    "clean black ink contours, soft pastel flat color blocks, "
    "warm off-white minimalist background, crisp visual metaphor, "
    "clean graphic design aesthetic, 8k resolution, masterpiece, no photorealism, no 3D render"
)

def generate_handdraw_illustration(prompt_subject: str, output_path: str, ratio: str = "3:4", size: str = "2K") -> str:
    """
    Generate a style-locked handdraw illustration using agnes-image-2.5-flash.
    Supports API Key pooling, rate-limit backoff, and local caching.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Check cache
    if output_file.exists() and output_file.stat().st_size > 20000:
        print(f"  [HanddrawProducer Cache] Reusing existing illustration: {output_file.name}")
        return str(output_file)

    full_prompt = f"{HANDDRAW_STYLE_ANCHOR}. {prompt_subject}"
    keys = get_agnes_keys()
    if not keys:
        raise RuntimeError("No Agnes API keys configured in .env!")

    print(f"  [HanddrawProducer] Requesting illustration via agnes-image-2.5-flash...")
    print(f"  [Prompt Summary] {prompt_subject[:80]}...")

    endpoint = "https://apihub.agnes-ai.com/v1/images/generations"
    
    for attempt in range(12):
        api_key = get_available_key(keys, resource_type="image")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "agnes-image-2.5-flash",
            "prompt": full_prompt,
            "size": size,
            "ratio": ratio,
            "extra_body": {
                "response_format": "url"
            }
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                
                url = None
                if "data" in res and len(res["data"]) > 0:
                    url = res["data"][0].get("url")
                elif "url" in res:
                    url = res.get("url")

                if url:
                    print(f"  [HanddrawProducer] Image generated successfully. Downloading -> {output_file.name}")
                    dl_cmd = ["curl", "-s", "-o", str(output_file), url]
                    subprocess.run(dl_cmd, check=True)
                    return str(output_file)
                else:
                    print(f"  [HanddrawProducer Warning] URL missing in response: {res}")
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            print(f"  [HanddrawProducer HTTP {err.code}] {err_body[:120]}")
            if err.code in [429, 503] or "rate limit" in err_body.lower():
                record_429(api_key, resource_type="image")
                time.sleep(3)
                continue
        except Exception as e:
            print(f"  [HanddrawProducer Exception] {e}")
            time.sleep(2)
            continue

    raise RuntimeError(f"Failed to generate handdraw illustration after 12 retries for: {output_path}")

def format_handdraw_scene_for_render(source_img_path: str, target_png_path: str, target_size=(900, 1200)):
    """Standardize image dimensions and format for sweety-handdraw rendering."""
    im = Image.open(source_img_path).convert("RGB")
    im.resize(target_size, Image.Resampling.LANCZOS).save(target_png_path)
    print(f"  ✓ Standardized {Path(target_png_path).name} to {target_size[0]}x{target_size[1]}")
