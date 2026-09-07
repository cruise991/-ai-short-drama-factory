#!/usr/bin/env python3
"""AI Short Drama Factory - Unified Main Entry Point.

Provides a unified command-line and interactive launcher for:
  - Agentic Orchestrator (Interactive Multi-Turn Drama & Video Production)
  - FastAPI Backend Service (REST API, WebSocket, Static Media Server)
  - Workspace Hygiene & Maintenance (Cache cleanup & disk health audit)

Usage:
  python3 main.py          # Launch interactive navigation menu
  python3 main.py --cli    # Launch CLI Orchestrator directly
  python3 main.py --server # Launch FastAPI backend server directly
  python3 main.py --status # View workspace disk usage & hygiene report
  python3 main.py --clean  # Safely clean temporary cache files
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def start_orchestrator():
    """Launch the Agentic QA Orchestrator."""
    print("\n🎬 正在启动 [AI 短剧全局智能调度与质检编排器] (Orchestrator)...")
    orch_path = BASE_DIR / "orchestrator.py"
    subprocess.run([sys.executable, str(orch_path)], cwd=str(BASE_DIR))


def start_backend(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Launch FastAPI backend server using uvicorn."""
    print(f"\n🚀 正在启动 [FastAPI 媒体与业务后端服务] on http://{host}:{port}...")
    server_dir = BASE_DIR / "server"
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", host,
        "--port", str(port),
    ]
    if reload:
        cmd.append("--reload")
    
    env = os.environ.copy()
    # Add server to PYTHONPATH so that api.main can import internal modules smoothly
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{server_dir}:{BASE_DIR}:{current_pythonpath}"
    
    try:
        subprocess.run(cmd, cwd=str(server_dir), env=env)
    except KeyboardInterrupt:
        print("\n🛑 后端服务已安全停止。")


def run_workspace_clean(dry_run: bool = False):
    """Trigger the workspace cleaner script."""
    clean_script = BASE_DIR / "scripts" / "clean_workspace.py"
    cmd = [sys.executable, str(clean_script)]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--execute")
    subprocess.run(cmd, cwd=str(BASE_DIR))


def show_workspace_status():
    """Trigger the workspace status check."""
    clean_script = BASE_DIR / "scripts" / "clean_workspace.py"
    subprocess.run([sys.executable, str(clean_script), "--status"], cwd=str(BASE_DIR))


def start_fullstack_dev():
    """Launch both FastAPI backend and Vite frontend concurrently."""
    print("\n⚡ 正在以并发模式拉起【全栈开发环境】 (FastAPI Backend + Vite Frontend)...")
    server_dir = BASE_DIR / "server"
    frontend_dir = BASE_DIR / "frontend"
    
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{server_dir}:{BASE_DIR}:{current_pythonpath}"
    
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(server_dir),
        env=env
    )
    
    # Check if npm / npx exists
    import shutil
    has_npm = shutil.which("npm") is not None
    frontend_proc = None
    if has_npm and (frontend_dir / "package.json").exists():
        print("🚀 启动 Vite 前端开发服务器 (http://localhost:5173)...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir)
        )
    else:
        print("⚠️ 未检测到 npm 环境，仅启动后端服务。")

    print("\n✅ 全栈服务已就绪: 前端 http://localhost:5173 | 后端 http://localhost:8000 (按 Ctrl+C 停止)")
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 正在停止全栈服务...")
        backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("全栈服务已安全停止。")


def interactive_menu():
    """Display interactive CLI menu."""
    while True:
        print("\n" + "=" * 55)
        print("🎬  AI Short Drama Factory - 统一主控台 (Unified Portal)")
        print("=" * 55)
        print("  1. 🤖 启动【短剧与智能体调度器】(CLI Orchestrator)")
        print("  2. 🌐 启动【FastAPI 业务与媒体后端】(Port 8000)")
        print("  3. ⚡ 启动【全栈开发环境】(Backend + Vite Frontend)")
        print("  4. 🔍 查看【工作区存储与健康状态】(Workspace Status)")
        print("  5. 🧹 执行【工作区缓存与临时文件清理】(Clean Workspace)")
        print("  0. 🚪 退出 (Exit)")
        print("=" * 55)
        
        try:
            choice = input("请选择操作 [0-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break
            
        if choice == "1":
            start_orchestrator()
        elif choice == "2":
            start_backend()
        elif choice == "3":
            start_fullstack_dev()
        elif choice == "4":
            show_workspace_status()
        elif choice == "5":
            run_workspace_clean(dry_run=False)
        elif choice in ("0", "q", "quit", "exit"):
            print("已退出统一主控台。")
            break
        else:
            print("⚠️ 无效输入，请重新选择。")


def main():
    parser = argparse.ArgumentParser(description="AI Short Drama Factory - Unified Main Entry")
    parser.add_argument("--cli", action="store_true", help="Launch CLI Orchestrator directly")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI backend directly")
    parser.add_argument("--dev", action="store_true", help="Launch fullstack dev environment (Backend + Frontend)")
    parser.add_argument("--status", action="store_true", help="View workspace health and disk usage")
    parser.add_argument("--clean", action="store_true", help="Execute safe workspace ephemeral cleanup")
    parser.add_argument("--host", default="0.0.0.0", help="FastAPI host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="FastAPI port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable uvicorn auto-reload")
    
    args = parser.parse_args()
    
    if args.cli:
        start_orchestrator()
    elif args.server:
        start_backend(host=args.host, port=args.port, reload=not args.no_reload)
    elif args.dev:
        start_fullstack_dev()
    elif args.status:
        show_workspace_status()
    elif args.clean:
        run_workspace_clean(dry_run=False)
    else:
        interactive_menu()



if __name__ == "__main__":
    main()
