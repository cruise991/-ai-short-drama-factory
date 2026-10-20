import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure server path is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from models.database import create_db_and_tables, engine, Project
from sqlmodel import Session, select

@pytest.fixture(scope="module")
def client():
    create_db_and_tables()
    with TestClient(app) as test_client:
        yield test_client

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_project_create_and_detail_workflow(client):
    test_slug = "test-workflow-automation-slug"
    test_goal = "测试全流程自动化剧本项目"

    payload = {
        "goal": test_goal,
        "slug": test_slug,
        "format_type": "standard_vertical_drama"
    }

    # 1. Test unauthenticated request is rejected with 401
    unauth_res = client.post("/api/projects", json=payload)
    assert unauth_res.status_code == 401

    # 2. Register & login test operator to obtain valid token
    client.post("/api/auth/register", json={
        "username": "workflow_tester",
        "password": "WorkflowPassword123!"
    })
    login_res = client.post("/api/auth/login", json={
        "username": "workflow_tester",
        "password": "WorkflowPassword123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clean up if existed
    with Session(engine) as session:
        existing = session.exec(select(Project).where(Project.project_slug == test_slug)).first()
        if existing:
            session.delete(existing)
            session.commit()

    # 3. Test creation via authenticated JSON Body
    create_res = client.post("/api/projects", json=payload, headers=headers)
    assert create_res.status_code == 200
    proj_data = create_res.json()
    actual_slug = proj_data["project_slug"]
    assert actual_slug.startswith("测试全流程自动化剧本项目")
    proj_id = proj_data["id"]

    # 4. Test get project detail with auth
    detail_res = client.get(f"/api/projects/{actual_slug}/detail", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["project"]["project_slug"] == actual_slug
    assert "current_status" in detail_data
    assert "is_waiting_approval" in detail_data
    assert detail_data["is_waiting_approval"] is False

    # 5. Test approve/reject when not pending
    reject_res = client.post(f"/api/projects/{proj_id}/reject", json={"message": "修改开场节奏"}, headers=headers)
    assert reject_res.status_code == 200
    assert reject_res.json()["success"] is False

    # 6. Test approve/reject with active future in PENDING_INPUTS
    import asyncio
    from api.routes.projects import PENDING_INPUTS
    loop = asyncio.new_event_loop()
    PENDING_INPUTS[proj_id] = loop.create_future()

    detail_pending = client.get(f"/api/projects/{actual_slug}/detail", headers=headers).json()
    assert detail_pending["is_waiting_approval"] is True

    # Test rejection feedback resolution
    rej_active = client.post(f"/api/projects/{proj_id}/reject", json={"message": "请增加主角反击情绪"}, headers=headers)
    assert rej_active.status_code == 200
    assert rej_active.json()["success"] is True
    assert PENDING_INPUTS[proj_id].result() == "请增加主角反击情绪"

    # Test approve resolution
    PENDING_INPUTS[proj_id] = loop.create_future()
    appr_active = client.post(f"/api/projects/{proj_id}/approve", headers=headers)
    assert appr_active.status_code == 200
    assert appr_active.json()["success"] is True
    assert PENDING_INPUTS[proj_id].result() == "ok"

    if proj_id in PENDING_INPUTS:
        del PENDING_INPUTS[proj_id]
    loop.close()

    # Cleanup
    with Session(engine) as session:
        p = session.get(Project, proj_id)
        if p:
            session.delete(p)
            session.commit()
