import requests

url = "https://apihub.agnes-ai.com/agnesapi?video_id=task_kyTFYzZlrta3BbcGdiAutbljPrrpK93L"
try:
    resp = requests.get(url, timeout=30)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
