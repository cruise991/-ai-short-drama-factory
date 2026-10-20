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
from models.database import create_db_and_tables, engine, User, UserRole

@pytest.fixture(scope="module")
def client():
    create_db_and_tables()
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def clean_users():
    # Clean up users before and after each test
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for u in users:
            session.delete(u)
        session.commit()
    yield
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for u in users:
            session.delete(u)
        session.commit()

def test_register_first_user_becomes_admin(client):
    res = client.post("/api/auth/register", json={
        "username": "superadmin",
        "password": "Password123!",
        "email": "admin@example.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "superadmin"
    assert data["role"] == UserRole.ADMIN.value
    assert data["is_active"] is True
    assert "id" in data

def test_register_subsequent_user_becomes_operator(client):
    # First user
    client.post("/api/auth/register", json={
        "username": "admin_one",
        "password": "Password123!"
    })
    # Second user
    res = client.post("/api/auth/register", json={
        "username": "operator_one",
        "password": "Password123!",
        "email": "operator@example.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "operator_one"
    assert data["role"] == UserRole.OPERATOR.value

def test_register_duplicate_username_fails(client):
    client.post("/api/auth/register", json={
        "username": "alice",
        "password": "Password123!"
    })
    res2 = client.post("/api/auth/register", json={
        "username": "alice",
        "password": "Password456!"
    })
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"]

def test_login_success_and_wrong_password(client):
    # Register user
    client.post("/api/auth/register", json={
        "username": "bob",
        "password": "SecretPassword!"
    })
    # Correct login
    login_res = client.post("/api/auth/login", json={
        "username": "bob",
        "password": "SecretPassword!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["username"] == "bob"

    # Wrong password
    bad_login = client.post("/api/auth/login", json={
        "username": "bob",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

def test_protected_routes_and_rbac(client):
    # 1. Register admin
    client.post("/api/auth/register", json={
        "username": "ceo_admin",
        "password": "AdminPassword!"
    })
    admin_token = client.post("/api/auth/login", json={
        "username": "ceo_admin",
        "password": "AdminPassword!"
    }).json()["access_token"]

    # 2. Register operator
    client.post("/api/auth/register", json={
        "username": "worker_user",
        "password": "WorkerPassword!"
    })
    worker_token = client.post("/api/auth/login", json={
        "username": "worker_user",
        "password": "WorkerPassword!"
    }).json()["access_token"]

    # 3. /api/auth/me without auth header -> 401
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # 4. /api/auth/me with worker token -> 200
    worker_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {worker_token}"})
    assert worker_me.status_code == 200
    assert worker_me.json()["username"] == "worker_user"

    # 5. /api/auth/users (admin-only) with worker token -> 403
    forbidden_res = client.get("/api/auth/users", headers={"Authorization": f"Bearer {worker_token}"})
    assert forbidden_res.status_code == 403

    # 6. /api/auth/users with admin token -> 200
    admin_users = client.get("/api/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_users.status_code == 200
    assert len(admin_users.json()) == 2

    # 7. Token refresh
    refresh_res = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {worker_token}"})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
