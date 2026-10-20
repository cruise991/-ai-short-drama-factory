import os
import sys
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(BASE_DIR, "server")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from api.main import app
from models.database import create_db_and_tables, engine, User
from core.security import create_access_token

@pytest.fixture(scope="module")
def client():
    create_db_and_tables()
    with TestClient(app) as test_client:
        yield test_client

from middleware.rate_limit import limiter

@pytest.fixture(autouse=True)
def clean_users():
    limiter.reset()
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for u in users:
            session.delete(u)
        session.commit()
    yield
    limiter.reset()
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for u in users:
            session.delete(u)
        session.commit()

def test_cors_allowed_origin(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    }
    res = client.options("/api/health", headers=headers)
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"

def test_cors_disallowed_origin(client):
    headers = {
        "Origin": "http://evil-attacker.example.com",
        "Access-Control-Request-Method": "GET"
    }
    res = client.options("/api/health", headers=headers)
    assert res.headers.get("access-control-allow-origin") != "http://evil-attacker.example.com"

def test_expired_jwt_rejected(client):
    # Register user
    client.post("/api/auth/register", json={
        "username": "exp_user",
        "password": "Password123!"
    })
    # Create already expired token (-1 minute)
    expired_token = create_access_token(
        data={"sub": "exp_user", "role": "operator"},
        expires_delta=timedelta(minutes=-1)
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "token expired" in res.json()["detail"].lower() or "credentials" in res.json()["detail"].lower()

def test_tampered_jwt_rejected(client):
    client.post("/api/auth/register", json={
        "username": "tamper_user",
        "password": "Password123!"
    })
    valid_token = client.post("/api/auth/login", json={
        "username": "tamper_user",
        "password": "Password123!"
    }).json()["access_token"]

    # Corrupt token
    tampered_token = valid_token[:-4] + "fake"
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401

def test_rate_limit_exceeded(client):
    # /api/auth/login is limited to 10/minute
    # Send 15 requests in rapid succession
    status_codes = []
    for _ in range(15):
        res = client.post("/api/auth/login", json={
            "username": "nonexistent_rate_user",
            "password": "WrongPassword!"
        })
        status_codes.append(res.status_code)
    
    # At least one request should be 429
    assert 429 in status_codes
    rate_limited_idx = status_codes.index(429)
    # Check 429 response structure
    res_429 = client.post("/api/auth/login", json={
        "username": "nonexistent_rate_user",
        "password": "WrongPassword!"
    })
    if res_429.status_code == 429:
        assert res_429.json()["error"] == "RateLimitExceeded"
