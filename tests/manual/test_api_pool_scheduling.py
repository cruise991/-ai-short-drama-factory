import sys
import os
import json
import time

# Add project root to path
workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from shared_tools.api_pool import get_agnes_keys, get_available_key, record_429, USAGE_FILE

def main():
    # Clear usage file
    with open(USAGE_FILE, "w") as f:
        json.dump({}, f)

    keys = get_agnes_keys()
    print(f"Loaded {len(keys)} keys.")
    if len(keys) == 0:
        print("No keys found. Please check .env")
        return

    print("\n--- Testing text resource scheduling (140 requests) ---")
    counts = {k["key"]: 0 for k in keys}
    try:
        # Total text capacity = 5 * 20 + 40 = 140
        for i in range(140):
            key = get_available_key(keys, resource_type="text")
            counts[key] += 1
    except Exception as e:
        print(f"Error: {e}")

    print("Distribution of 140 requests:")
    for k, v in counts.items():
        print(f"Key {k[:10]}... : {v}")

    print("\n--- Testing 429 rate limit block ---")
    # Expire all old timestamps by subtracting 61 seconds
    with open(USAGE_FILE, "r") as f:
        data = json.load(f)
    for k in data:
        for res in data[k]:
            data[k][res] = [t - 61 for t in data[k][res]]
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)

    # Block first key
    first_key = keys[0]["key"]
    print(f"Applying 429 block to {first_key[:10]}...")
    record_429(first_key, resource_type="text")
    
    key_got = get_available_key(keys, resource_type="text")
    print(f"Next available key: {key_got[:10]}... (should NOT be the blocked key)")

    print("\n--- Testing video resource scheduling (7 requests) ---")
    counts_video = {k["key"]: 0 for k in keys}
    try:
        # Total video capacity = 5 * 1 + 2 = 7
        for i in range(7):
            key = get_available_key(keys, resource_type="video")
            counts_video[key] += 1
    except Exception as e:
        print(f"Error: {e}")

    print("Distribution of 7 video requests:")
    for k, v in counts_video.items():
        print(f"Key {k[:10]}... : {v}")

if __name__ == "__main__":
    main()
