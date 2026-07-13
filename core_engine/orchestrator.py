import json
import os
from typing import TypedDict, Annotated, List, Dict, Any

# Mock LangGraph imports for blueprint demonstration
# In a real environment, you'd run: pip install langgraph
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    # Creating mock classes to allow the file to run without dependencies during bootstrap
    class StateGraph:
        def __init__(self, state_schema): self.schema = state_schema; self.nodes = {}; self.edges = []
        def add_node(self, name, func): self.nodes[name] = func
        def add_edge(self, start, end): self.edges.append((start, end))
        def add_conditional_edges(self, start, condition, mapping): pass
        def set_entry_point(self, name): self.entry = name
        def compile(self, checkpointer=None, interrupt_before=None): return self
    END = "END"
    MemorySaver = lambda: None

# --- 1. Define State (状态定义) ---
class CompanyState(TypedDict):
    ticket_id: str
    goal: str
    current_status: str
    script_content: str
    qa_feedback: str
    reject_count: int
    final_video_path: str

# --- 2. Define Department Nodes (部门节点定义) ---

def planning_dept_node(state: CompanyState) -> CompanyState:
    print(f"[Planning Dept] Processing ticket: {state['ticket_id']}")
    # Mocking RAG and Web Search to generate script
    new_script = f"Script generated based on goal: {state['goal']} (Version {state['reject_count'] + 1})"
    if state.get("qa_feedback"):
        print(f"[Planning Dept] Incorporating feedback: {state['qa_feedback']}")
        new_script += f" | Addressed feedback: {state['qa_feedback']}"
    
    state["script_content"] = new_script
    state["current_status"] = "Script_Drafted"
    return state

def human_approval_node(state: CompanyState) -> CompanyState:
    # This node acts as a dummy node. LangGraph will interrupt BEFORE this node executes.
    # When the user clicks "Approve" or "Reject" in the Streamlit UI, they will update the state
    # and resume the graph.
    print("[CEO Dashboard] Received human input.")
    return state

def production_dept_node(state: CompanyState) -> CompanyState:
    print("[Production Dept] Generating assets (ComfyUI / Kling / FishSpeech)...")
    # Mock generating assets
    state["current_status"] = "Assets_Generated"
    return state

def qa_evolution_dept_node(state: CompanyState) -> CompanyState:
    print("[QA Dept] Auditing video assets using VLM...")
    # Mock QA process
    # Let's say if reject_count is 0, we force a reject to test the loop
    if state["reject_count"] < 1:
        print("[QA Dept] ❌ Detection: Character face distortion. Rejecting!")
        state["qa_feedback"] = "Character face is distorted at 00:03. Fix the prompt."
        state["reject_count"] += 1
        state["current_status"] = "QA_Rejected"
    else:
        print("[QA Dept] ✅ Video passed audit. Merging...")
        state["final_video_path"] = f"projects/{state['ticket_id']}/03_final_video/output.mp4"
        state["current_status"] = "Completed"
    
    return state

# --- 3. Define Conditional Edges (路由条件) ---

def check_human_approval(state: CompanyState) -> str:
    # The UI will set qa_feedback if rejected
    if state.get("qa_feedback") and "human_reject" in state.get("qa_feedback", ""):
        return "planning_dept" # Back to planning
    return "production_dept" # Approved, go to production

def check_qa_status(state: CompanyState) -> str:
    if state["current_status"] == "QA_Rejected":
        return "production_dept" # Normally back to production to re-roll
    return END

# --- 4. Build the Graph (构建公司运转图) ---
def build_company_graph():
    workflow = StateGraph(CompanyState)
    
    workflow.add_node("planning_dept", planning_dept_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("production_dept", production_dept_node)
    workflow.add_node("qa_dept", qa_evolution_dept_node)
    
    workflow.set_entry_point("planning_dept")
    
    workflow.add_edge("planning_dept", "human_approval")
    # Conditional edge from human approval
    workflow.add_conditional_edges(
        "human_approval",
        check_human_approval,
        {"planning_dept": "planning_dept", "production_dept": "production_dept"}
    )
    
    workflow.add_edge("production_dept", "qa_dept")
    
    # Conditional edge from QA
    workflow.add_conditional_edges(
        "qa_dept",
        check_qa_status,
        {"production_dept": "production_dept", END: END}
    )
    
    # Compile with memory checkpointing to enable Human-in-the-Loop interruptions
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_approval"])
    return app

if __name__ == "__main__":
    print("AutoMedia Virtual Company Core Engine Initialized.")
    graph = build_company_graph()
    print("Graph compiled successfully. Ready for tickets.")
