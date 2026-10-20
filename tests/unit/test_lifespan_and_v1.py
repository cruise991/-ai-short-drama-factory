import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from models.database import create_db_and_tables, engine, User

@pytest.fixture(scope="module")
def client():
    create_db_and_tables()
    with TestClient(app) as test_client:
        yield test_client

def test_v1_and_legacy_health_endpoints(client):
    # Test v1 health
    v1_res = client.get("/api/v1/health")
    assert v1_res.status_code == 200
    v1_data = v1_res.json()
    assert v1_data["status"] == "ok"
    assert v1_data["version"] == "v1.0.0"
    assert "RESTful v1" in v1_data["api_standard"]

    # Test legacy health
    legacy_res = client.get("/api/health")
    assert legacy_res.status_code == 200
    legacy_data = legacy_res.json()
    assert legacy_data["status"] == "ok"

def test_v1_auth_flow(client):
    # Clean up test user
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == "v1_user")).first()
        if existing:
            session.delete(existing)
            session.commit()

    # Register via /api/v1/auth/register
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "v1_user",
        "password": "Password123!",
        "email": "v1@example.com"
    })
    assert reg_res.status_code == 200
    assert reg_res.json()["username"] == "v1_user"

    # Login via /api/v1/auth/login
    login_res = client.post("/api/v1/auth/login", json={
        "username": "v1_user",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # Get profile via /api/v1/auth/me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "v1_user"

    # Clean up
    with Session(engine) as session:
        u = session.exec(select(User).where(User.username == "v1_user")).first()
        if u:
            session.delete(u)
            session.commit()

from middleware.rate_limit import limiter
from core.security import create_access_token

@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.reset()
    yield
    limiter.reset()

def test_global_exception_handler(client):
    token = create_access_token(data={"sub": "admin_crash_tester", "role": "admin"})

    # Dynamically mount an intentional error route to test the handler
    @app.get("/api/test-crash")
    def intentional_crash():
        raise RuntimeError("Intentional crash for testing error handler")

    with TestClient(app, raise_server_exceptions=False) as crash_client:
        res = crash_client.get("/api/test-crash", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 500
        data = res.json()
        assert data["error"] == "InternalServerError"
        assert "error_id" in data
        assert "Intentional crash" in data["detail"]
