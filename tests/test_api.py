import os
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

# Prevent network side effects in tests.
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["ALLOWED_ORIGINS"] = "https://invisi-scan-three.vercel.app,http://localhost:5174"

from backend.api import app

client = TestClient(app)


def _fresh_username() -> str:
    return f"testuser_{int(time.time() * 1000)}"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Invisi-Scan API is running"}


def test_register_login_flow():
    username = _fresh_username()
    password = "testpass123"

    register_res = client.post("/api/register", json={"username": username, "password": password})
    assert register_res.status_code == 200
    assert register_res.json()["ok"] is True

    login_res = client.post("/api/login", json={"username": username, "password": password})
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["ok"] is True
    assert "token" in data
    assert data["role"] == "operator"
    assert data["username"] == username


def test_register_cannot_set_admin_role():
    username = _fresh_username()
    password = "testpass123"
    res = client.post(
        "/api/register",
        json={"username": username, "password": password, "role": "admin"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True

    login_res = client.post("/api/login", json={"username": username, "password": password})
    assert login_res.status_code == 200
    assert login_res.json().get("role") == "operator"


def test_validation_and_auth_guards():
    bad_login = client.post("/api/login", json={"username": "", "password": "123"})
    assert bad_login.status_code == 422

    bad_register = client.post("/api/register", json={"username": "ab", "password": "12345"})
    assert bad_register.status_code == 422

    schedule_without_auth = client.post("/api/schedule", json={"target": "example.com", "interval": 24})
    assert schedule_without_auth.status_code in {401, 403}


def test_google_auth_requires_id_token():
    response = client.post("/api/auth/google", json={})
    assert response.status_code == 422


def test_google_auth_blank_id_token_rejected():
    response = client.post("/api/auth/google", json={"id_token": "   "})
    assert response.status_code == 422


def test_google_auth_timeout_returns_friendly_error(monkeypatch):
    async def fake_get(self, *args, **kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    response = client.post("/api/auth/google", json={"id_token": "fake-token"})
    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "error": "Google sign-in timed out. Please try again.",
    }


def test_cors_preflight_for_known_origin():
    response = client.options(
        "/api/auth/google",
        headers={
            "Origin": "https://invisi-scan-three.vercel.app",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://invisi-scan-three.vercel.app"
