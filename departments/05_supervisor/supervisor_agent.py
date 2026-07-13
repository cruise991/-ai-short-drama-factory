import os
import json
import time
import glob

class SupervisorAgent:
    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir
        self.projects_dir = os.path.join(workspace_dir, "projects")
        
        # State mapping to completion percentage
        self.progress_map = {
            "Drafting": 10,
            "Draft_Completed": 40,
            "Assets_Generated": 70,
            "Completed": 90, # Completed the QA phase, but wait... where is the final video?
            "Final_Assembly_Done": 100
        }

    def scan_projects(self):
        print(f"\n[{time.strftime('%H:%M:%S')}] [Supervisor Dept] Scanning all projects for idle tasks...")
        
        # Find all task tickets
        ticket_files = glob.glob(os.path.join(self.projects_dir, "*/*", "00_task_ticket.json"))
        
        if not ticket_files:
            print("[Supervisor Dept] No active task tickets found.")
            return

        for ticket_path in ticket_files:
            self._process_ticket(ticket_path)

    def _process_ticket(self, ticket_path):
        episode_dir = os.path.dirname(ticket_path)
        episode_name = os.path.basename(episode_dir)
        
        try:
            with open(ticket_path, "r", encoding="utf-8") as f:
                ticket = json.load(f)
        except Exception as e:
            print(f"[Supervisor Dept] Error reading ticket {ticket_path}: {e}")
            return

        status = ticket.get("status", "Unknown")
        progress = self.progress_map.get(status, 0)
        
        print(f"  -> Project: [{episode_name}] | Status: {status} | Progress: {progress}%")
        
        # --- Task Scheduling & Tool Allocation Logic ---
        
        if status == "Drafting":
            print("     [Action] Task is in Drafting phase. Dispatching to Planning Dept...")
            # Here we would programmatically call planning_agent.process_ticket()
            
        elif status == "Draft_Completed":
            print("     [Action] Draft is approved. Idle state detected. Dispatching to Production Dept...")
            # Here we would programmatically call production_agent.process_ticket()
            
        elif status == "Assets_Generated":
            print("     [Action] Assets are generated. Idle state detected. Dispatching to QA Dept...")
            # Here we would programmatically call qa_agent.process_ticket()
            
        elif status == "Completed":
            print("     [Warning] QA is completed, but Final Assembly is pending!")
            print("     [TOOL ALERT] The system lacks an 'Audio Sync & Video Compositing' MCP Tool.")
            print("     [TOOL ALERT] Requesting CEO to provision tools for: FFmpeg / CapCut API.")
            
            # Write a missing tools alert to the directory for the UI to pick up
            alert_path = os.path.join(episode_dir, "04_MISSING_TOOL_ALERT.md")
            if not os.path.exists(alert_path):
                with open(alert_path, "w", encoding="utf-8") as f:
                    f.write("# 🔴 [URGENT] Missing Tool Alert\n\n")
                    f.write("Supervisor Agent has halted the pipeline for this project.\n")
                    f.write("**Reason**: Assets are generated and QA passed, but we lack the final Video Assembly Tool (e.g., FFmpeg integration or TTS audio generator) to stitch the assets together.\n")
                    f.write("**Request**: Please provide a script or MCP tool for Audio & Video composition.")
                print(f"     [Action] Generated Tool Request Alert at {alert_path}")
        
        elif status == "Final_Assembly_Done":
            print("     [Action] Project is completely finished and ready for distribution.")

def run_daemon(workspace_dir):
    print("=========================================================")
    print(" 👁️  Progress & Tooling Supervisor Daemon Started")
    print("=========================================================")
    supervisor = SupervisorAgent(workspace_dir)
    
    # In a real environment, this would be a while True loop. 
    # For demonstration, we'll scan once to show the logic.
    supervisor.scan_projects()
    print("=========================================================\n")

if __name__ == "__main__":
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_daemon(workspace_dir)
