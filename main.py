import os
import subprocess
import threading
import time

def start_supervisor():
    """Starts the background Progress & Tooling Supervisor daemon."""
    print("🚀 [Main Entry] Starting Supervisor Daemon in background...")
    # In a real environment, this would call the supervisor loop directly or via subprocess
    supervisor_path = os.path.join(os.path.dirname(__file__), "departments", "05_supervisor", "supervisor_agent.py")
    subprocess.run(["python3", supervisor_path])

def start_web_ui():
    """Starts the Streamlit Web UI."""
    print("🚀 [Main Entry] Starting Web UI for CEO Dashboard...")
    ui_path = os.path.join(os.path.dirname(__file__), "web_ui", "app.py")
    # Streamlit typically runs on port 8501
    subprocess.run(["streamlit", "run", ui_path, "--server.port=8501", "--server.address=0.0.0.0"])

if __name__ == "__main__":
    print("==================================================")
    print("🎬 AI Short Drama Factory - Unified Entry Point 🎬")
    print("==================================================")
    
    # Thread 1: Background Supervisor (Polling projects directory)
    supervisor_thread = threading.Thread(target=start_supervisor, daemon=True)
    supervisor_thread.start()
    
    # Thread 2: Foreground Web UI (Blocks main thread)
    # Give supervisor a second to print its banner
    time.sleep(1)
    start_web_ui()
