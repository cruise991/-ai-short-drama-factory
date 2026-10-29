import os
import sys
import pytest
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from models.database import Project, Asset, Feedback, User, UserRole
from migrate_sqlite_to_pg import migrate_data

@pytest.fixture
def temp_db_paths(tmp_path):
    src_db = tmp_path / "src_test.db"
    dst_db = tmp_path / "dst_test.db"
    return str(src_db), f"sqlite:///{dst_db}"

def test_migration_pipeline(temp_db_paths):
    src_path, dst_url = temp_db_paths
    src_engine = create_engine(f"sqlite:///{src_path}")
    SQLModel.metadata.create_all(src_engine)

    # Populate test data in source DB
    with Session(src_engine) as session:
        user = User(
            id=1,
            username="migrate_test_user",
            hashed_password="hash",
            role=UserRole.ADMIN.value,
            is_active=True
        )
        proj = Project(
            id=10,
            project_slug="test_slug_migration",
            goal="测试数据库迁移",
            format_type="vertical",
            status="Draft_Completed"
        )
        asset = Asset(
            id=100,
            project_id=10,
            asset_type="video",
            shot_id="shot_01",
            s3_url="https://s3.example.com/shot_01.mp4"
        )
        feedback = Feedback(
            id=200,
            project_id=10,
            feedback_text="质量很好",
            target_phase="Draft_Completed"
        )
        session.add(user)
        session.add(proj)
        session.add(asset)
        session.add(feedback)
        session.commit()

    # 1. Test dry-run
    dry_success = migrate_data(src_path, dst_url, dry_run=True)
    assert dry_success is True

    # Destination should not have records yet
    dst_engine = create_engine(dst_url)
    SQLModel.metadata.create_all(dst_engine)
    with Session(dst_engine) as session:
        assert session.exec(select(User)).first() is None

    # 2. Test actual migration
    actual_success = migrate_data(src_path, dst_url, dry_run=False)
    assert actual_success is True

    # 3. Verify target database records and data integrity
    with Session(dst_engine) as session:
        migrated_user = session.get(User, 1)
        assert migrated_user is not None
        assert migrated_user.username == "migrate_test_user"
        assert migrated_user.role == UserRole.ADMIN.value
        assert migrated_user.tenant_id == "default"

        migrated_proj = session.get(Project, 10)
        assert migrated_proj is not None
        assert migrated_proj.project_slug == "test_slug_migration"
        assert migrated_proj.status == "Draft_Completed"
        assert migrated_proj.tenant_id == "default"

        migrated_asset = session.get(Asset, 100)
        assert migrated_asset is not None
        assert migrated_asset.project_id == 10
        assert migrated_asset.s3_url == "https://s3.example.com/shot_01.mp4"
        assert migrated_asset.tenant_id == "default"

        migrated_feedback = session.get(Feedback, 200)
        assert migrated_feedback is not None
        assert migrated_feedback.feedback_text == "质量很好"
        assert migrated_feedback.tenant_id == "default"
