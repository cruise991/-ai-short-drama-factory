#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Short Drama Factory - 系统状态、SQLite 数据库与工作区全局规则快照备份工具
功能：
1. SQLite 热快照备份 (在线无锁备份，生成 archive/backups/app_YYYYMMDD_HHMM.db)
2. 导出项目与任务表至 JSON (方便跨平台迁移与审计)
3. 自动镜像父级 /Users/workspace/ai_short_company/.agents/AGENTS.md 至版本控制区
"""

import os
import sys
import shutil
import sqlite3
import json
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(REPO_ROOT, ".."))

DB_PATH = os.path.join(REPO_ROOT, "server", "data", "app.db")
BACKUP_DIR = os.path.join(REPO_ROOT, "archive", "backups")
RULES_BACKUP_DIR = os.path.join(REPO_ROOT, "docs", "rules")

def backup_sqlite():
    if not os.path.exists(DB_PATH):
        print(f"ℹ️ SQLite 数据库尚未初始化或不存在于: {DB_PATH}")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_db = os.path.join(BACKUP_DIR, f"app_{timestamp}.db")

    print(f"📦 [1/3] 正在对 SQLite 执行在线安全热备份...")
    try:
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(target_db)
        with dst_conn:
            src_conn.backup(dst_conn)
        src_conn.close()
        dst_conn.close()
        size_kb = os.path.getsize(target_db) / 1024
        print(f"  ✅ SQLite 备份成功 -> {target_db} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"  ❌ SQLite 备份失败: {e}")

    # 导出可读 JSON
    try:
        print(f"📄 [2/3] 正在导出结构化数据快照至 JSON...")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]

        dump_data = {"exported_at": datetime.now().isoformat(), "tables": {}}
        for tbl in tables:
            cursor.execute(f"SELECT * FROM {tbl};")
            rows = [dict(r) for r in cursor.fetchall()]
            dump_data["tables"][tbl] = rows

        conn.close()

        json_path = os.path.join(BACKUP_DIR, "db_export_latest.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON 结构化数据导出成功 -> {json_path}")
    except Exception as e:
        print(f"  ⚠️ JSON 导出跳过: {e}")

def backup_workspace_rules():
    parent_agents_md = os.path.join(WORKSPACE_ROOT, ".agents", "AGENTS.md")
    if os.path.exists(parent_agents_md):
        print(f"🛡️ [3/3] 正在同步父级工作区系统规则 (AGENTS.md)...")
        os.makedirs(RULES_BACKUP_DIR, exist_ok=True)
        dest_md = os.path.join(RULES_BACKUP_DIR, "WORKSPACE_AGENTS.md")
        shutil.copy2(parent_agents_md, dest_md)
        print(f"  ✅ 父级规则已镜像归档至 -> {dest_md}")
    else:
        print("  ℹ️ 未检测到父级 .agents/AGENTS.md，跳过规则镜像。")

if __name__ == "__main__":
    print("==================================================")
    print("🚀 AI Short Drama Factory — 系统状态与数据安全快照")
    print("==================================================")
    backup_sqlite()
    backup_workspace_rules()
    print("==================================================")
    print("🎉 系统快照备份流程执行完成！")
    print("==================================================")
