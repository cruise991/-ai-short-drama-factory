import sys
import os
import importlib

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
production_agent = importlib.import_module("departments.03_production.production_agent")

shot = {
    "id": "beat1",
    "video_prompt": "Luna dances",
    "image_suggestion": "Luna looking back",
    "reference_image": "luna.png"
}
ticket = {
    "workflow_type": "dance_video",
    "style": "K-pop aesthetic",
    "locks": {
        "character_anchor": "Luna, a beautiful dancer",
        "costume_lock": "denim skirt",
        "scene_lock": "studio",
        "image_suggestion_full": ""
    }
}
production_agent.ticket = ticket
production_agent.is_dance = True
production_agent.locks = ticket["locks"]
production_agent.config = {}

# Patch _curl_request so it doesn't really call the API
def mock_curl_request(method, url, headers=None, json_data=None):
    print("MOCK API CALL:", url)
    print("DATA:", json_data)
    if "images" in url:
        return {"data": [{"url": "http://mock-image.png"}]}
    else:
        return {"video_id": "vid123"}
        
production_agent._curl_request = mock_curl_request

production_agent.process_single_shot(shot)
