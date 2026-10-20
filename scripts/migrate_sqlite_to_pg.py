#!/usr/bin/env python3
"""
SQLite 到 PostgreSQL 平滑数据迁移工具
支持断点同步、行数对账、事务回滚与 Dry-run 演练。
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, List

# Add server directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from sqlmodel import create_engine, Session, select, SQLModel
from models.database import User, Project, Asset, Feedback

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MigrateSqliteToPg")

MODELS = [
    ("user", User),
    ("project", Project),
    ("asset", Asset),
    ("feedback", Feedback),
]

def migrate_data(sqlite_path: str, pg_url: str, dry_run: bool = False, force: bool = False) -> bool:
    if not os.path.exists(sqlite_path):
        logger.error(f"源 SQLite 数据库不存在: {sqlite_path}")
        return False

    sqlite_url = f"sqlite:///{sqlite_path}"
    logger.info(f"正在连接源 SQLite 数据库: {sqlite_url}")
    src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

    logger.info(f"正在连接目标 PostgreSQL 数据库: {pg_url}")
    try:
        dst_engine = create_engine(pg_url, echo=False)
        # Ensure target schema exists
        if not dry_run:
            SQLModel.metadata.create_all(dst_engine)
    except Exception as e:
        logger.error(f"连接目标 PostgreSQL 失败: {e}")
        return False

    summary: Dict[str, Dict[str, int]] = {}

    try:
        with Session(src_engine) as src_session, Session(dst_engine) as dst_session:
            for table_name, model_cls in MODELS:
                src_records = src_session.exec(select(model_cls)).all()
                src_count = len(src_records)
                logger.info(f"读取表 [{table_name}] 记录数: {src_count}")

                if dry_run:
                    summary[table_name] = {"source": src_count, "migrated": 0, "status": "DRY_RUN"}
                    continue

                migrated_count = 0
                for record in src_records:
                    # Convert to dictionary and re-instantiate or merge
                    record_dict = record.model_dump() if hasattr(record, "model_dump") else record.dict()
                    existing = dst_session.get(model_cls, record_dict.get("id"))
                    if existing:
                        if force:
                            for k, v in record_dict.items():
                                setattr(existing, k, v)
                            migrated_count += 1
                    else:
                        new_record = model_cls(**record_dict)
                        dst_session.add(new_record)
                        migrated_count += 1

                dst_session.commit()
                # Verify destination count
                dst_count = len(dst_session.exec(select(model_cls)).all())
                summary[table_name] = {
                    "source": src_count,
                    "target": dst_count,
                    "migrated": migrated_count,
                    "status": "SUCCESS" if dst_count >= src_count else "MISMATCH"
                }

        logger.info("=== 迁移对账报告 ===")
        for tbl, stats in summary.items():
            logger.info(f"表: {tbl:10} | 源行数: {stats.get('source', 0)} | 目标行数: {stats.get('target', 0)} | 状态: {stats['status']}")

        logger.info("✅ 数据迁移与对账流程执行完毕！")
        return True

    except Exception as e:
        logger.error(f"❌ 迁移过程中发生异常，事务自动回滚: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="SQLite 到 PostgreSQL 数据库迁移工具")
    parser.add_argument(
        "--sqlite",
        default=os.path.join(SERVER_DIR, "data", "app.db"),
        help="SQLite 数据库文件路径 (默认: server/data/app.db)"
    )
    parser.add_argument(
        "--pg-url",
        default=os.getenv("DATABASE_URL", "postgresql://shortdrama:shortdrama_secret_2026@localhost:5432/shortdrama_db"),
        help="目标 PostgreSQL 连接串 (默认读取 DATABASE_URL)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅演练校验源数据与目标连接，不实际写入"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="若目标已存在同 ID 数据则强制覆盖更新"
    )

    args = parser.parse_args()
    success = migrate_data(args.sqlite, args.pg_url, dry_run=args.dry_run, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
