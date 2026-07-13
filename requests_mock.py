class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass

def post(*args, **kwargs):
    print(f"  [Mock Requests] Intercepted POST to {args[0]}")
    return MockResponse({"choices": [{"message": {"content": "{}"}}]})

def get(*args, **kwargs):
    print(f"  [Mock Requests] Intercepted GET to {args[0]}")
    return MockResponse({"status": "success"})

class exceptions:
    class Timeout(Exception):
        pass
