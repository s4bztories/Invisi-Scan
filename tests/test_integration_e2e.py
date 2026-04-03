import os
import sys
import time

import pyotp
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["ALLOWED_ORIGINS"] = "https://invisi-scan-three.vercel.app,http://localhost:5174"

from backend import database
from backend.api import app, create_access_token

client = TestClient(app)


def _username(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000)}"


def _ensure_user(username: str, password: str = "testpass123", role: str = "operator"):
    db = database.SessionLocal()
    try:
        if not database.get_user_by_username(db, username):
            database.create_user(db, username, password, role)
    finally:
        db.close()


def _token_for(username: str) -> str:
    db = database.SessionLocal()
    try:
        user = database.get_user_by_username(db, username)
        assert user is not None
        return create_access_token(user)
    finally:
        db.close()


def test_schedule_owner_cannot_delete_another_users_scan():
    owner = _username("owner")
    attacker = _username("attacker")
    _ensure_user(owner)
    _ensure_user(attacker)

    owner_headers = {"Authorization": f"Bearer {_token_for(owner)}"}
    attacker_headers = {"Authorization": f"Bearer {_token_for(attacker)}"}

    create_res = client.post(
        "/api/schedule",
        json={"target": "scanme.nmap.org", "interval": 24},
        headers=owner_headers,
    )
    assert create_res.status_code == 200
    assert create_res.json()["ok"] is True

    owner_scans = client.get("/api/schedule", headers=owner_headers)
    assert owner_scans.status_code == 200
    created_scan_id = owner_scans.json()["scans"][0]["id"]

    delete_res = client.delete(f"/api/schedule/{created_scan_id}", headers=attacker_headers)
    assert delete_res.status_code == 404


def test_2fa_end_to_end_login_flow():
    username = _username("totp")
    password = "testpass123"
    _ensure_user(username, password=password, role="operator")

    login_res = client.post("/api/login", json={"username": username, "password": password})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["ok"] is True
    assert "token" in login_data

    headers = {"Authorization": f"Bearer {login_data['token']}"}
    setup_res = client.post("/api/2fa/setup", headers=headers)
    assert setup_res.status_code == 200
    setup_data = setup_res.json()
    assert setup_data["ok"] is True
    secret = setup_data["secret"]

    otp_code = pyotp.TOTP(secret).now()
    enable_res = client.post("/api/2fa/enable", json={"otp_code": otp_code}, headers=headers)
    assert enable_res.status_code == 200
    assert enable_res.json()["is_totp_enabled"] is True

    login_after = client.post("/api/login", json={"username": username, "password": password})
    assert login_after.status_code == 200
    login_after_data = login_after.json()
    assert login_after_data["ok"] is True
    assert login_after_data["otp_required"] is True

    verify_res = client.post(
        "/api/login/verify-otp",
        json={"otp_ticket": login_after_data["otp_ticket"], "otp_code": pyotp.TOTP(secret).now()},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["ok"] is True
    assert "token" in verify_data


def test_observability_health_and_metrics():
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] in {"healthy", "degraded"}
    assert "uptime_seconds" in health_data

    admin_token = _token_for("admin")
    metrics_res = client.get("/api/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["ok"] is True
    assert "requests_total" in metrics
    assert "average_latency_ms" in metrics
    assert "status_counts" in metrics
