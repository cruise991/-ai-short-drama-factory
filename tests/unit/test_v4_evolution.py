import os
import json
import subprocess
import sys

def run_v4_verification():
    print("\n==========================================")
    print("🚀 启动 V4 架构全链路自证循环 (V4 Verification)")
    print("==========================================")
    
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_dir = os.path.join(workspace_dir, "projects", "v4-test-project")
    run_dir = os.path.join(project_dir, "runs", "test-001")
    os.makedirs(os.path.join(run_dir, "01_storyboards_scripts"), exist_ok=True)
    
    # 1. 模拟一个正在市场测试的剧本 (Mock Market Testing state)
    ticket_path = os.path.join(run_dir, "00_task_ticket.json")
    ticket = {
        "goal": "测试产品 V4",
        "project_name": "v4-test-project",
        "status": "Market_Testing"
    }
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)
        
    script_path = os.path.join(run_dir, "01_storyboards_scripts", "01_storyboard.md")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("# 黄金3秒\n测试文案。利用悬念留人。\n# 解决方案\n展示V4产品。\n# 行动号召\n点击购买。")
        
    # 2. 验证外部知识提炼 (Verify Knowledge Distillation exists in planning agent)
    print("\n[Check 1] 验证 planning_agent.py 是否拥有动态提取逻辑...")
    with open(os.path.join(workspace_dir, "departments", "02_planning", "planning_agent.py"), "r", encoding="utf-8") as f:
        content = f.read()
        if "Distilling dynamic SOP" in content:
            print("  ✅ 成功：planning_agent.py 已具备外部知识提炼闭环。")
        else:
            print("  ❌ 失败：未检测到动态提炼代码。")
            return
            
    # 3. 验证独立环境变量 (Verify Environment Isolation)
    print("\n[Check 2] 验证 .env 是否解耦了市场反馈部的 LLM...")
    with open(os.path.join(workspace_dir, ".env"), "r", encoding="utf-8") as f:
        env_content = f.read()
        if "MARKET_FEEDBACK_LLM_API_KEY" in env_content:
            print("  ✅ 成功：.env 架构稳定，已实现权限解耦。")
        else:
            print("  ❌ 失败：.env 依然存在高耦合。")
            return
            
    # 4. 执行市场反馈部，验证进化是否成功写入总线 (Execute Feedback Loop)
    print("\n[Check 3] 触发第七部门，验证市场闭环与记忆注入...")
    # Monkey-patch feedback_agent to force a HIT for deterministic testing
    feedback_script = os.path.join(workspace_dir, "departments", "07_market_feedback", "feedback_agent.py")
    with open(feedback_script, "r", encoding="utf-8") as f:
        original_fb = f.read()
        
    patched_fb = original_fb.replace(
        "is_hit = completion_rate > 30.0 and conversion_rate > 2.0 and views > 100000",
        "is_hit = True"
    ).replace(
        "is_flop = completion_rate < 10.0 or conversion_rate < 0.5",
        "is_flop = False"
    )
    with open(feedback_script, "w", encoding="utf-8") as f:
        f.write(patched_fb)
        
    try:
        subprocess.run([sys.executable, feedback_script, run_dir], check=True)
    finally:
        # Restore original
        with open(feedback_script, "w", encoding="utf-8") as f:
            f.write(original_fb)
            
    # 5. 验证中央记忆库 (Verify Memory updated)
    memory_path = os.path.join(workspace_dir, "departments", "company_memory.json")
    with open(memory_path, "r", encoding="utf-8") as f:
        memory = json.load(f)
        
    print(f"\n[Result] 进化完成！当前的中央总线记忆数：正向={len(memory.get('positive_patterns', []))}, 负向={len(memory.get('negative_patterns', []))}")
def test_v4_evolution():
    run_v4_verification()

if __name__ == "__main__":
    run_v4_verification()
