import queue

class InputManager:
    def __init__(self):
        self.project_queues = {}

    def register_project(self, project_id: int):
        self.project_queues[project_id] = queue.Queue()

    def unregister_project(self, project_id: int):
        if project_id in self.project_queues:
            del self.project_queues[project_id]

    def submit_input(self, project_id: int, user_input: str):
        if project_id in self.project_queues:
            self.project_queues[project_id].put(user_input)
            return True
        return False

    def wait_for_input(self, project_id: int, timeout: int = None) -> str:
        if project_id in self.project_queues:
            try:
                # This is blocking for the worker thread, which is fine!
                return self.project_queues[project_id].get(timeout=timeout)
            except queue.Empty:
                return ""
        return ""

input_manager = InputManager()
