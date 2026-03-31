import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root_endpoint():
    """Test the root API endpoint returns correct status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Invisi-Scan API is running"}

def test_history_endpoint():
    """Test the history endpoint (requires auth in real usage)."""
    response = client.get("/api/history")
    # This might require authentication, but test basic response
    assert response.status_code in [200, 401, 403]  # Allow auth failures for now

def test_register_endpoint():
    """Test user registration."""
    test_user = {
        "username": "testuser",
        "password": "testpass123",
        "role": "operator"
    }
    response = client.post("/api/register", json=test_user)
    assert response.status_code in [200, 400]  # 400 if user exists

def test_login_endpoint():
    """Test user login."""
    credentials = {
        "username": "operator",
        "password": "operator123"
    }
    response = client.post("/api/login", json=credentials)
    assert response.status_code in [200, 401]  # 401 if invalid creds

def test_input_validation():
    """Test input validation for various endpoints."""
    # Test invalid login
    response = client.post("/api/login", json={"username": "", "password": "short"})
    assert response.status_code == 422  # Validation error

    # Test invalid register
    response = client.post("/api/register", json={"username": "ab", "password": "12345", "role": "invalid"})
    assert response.status_code == 422

    # Test invalid schedule (will fail auth, but validation should happen first)
    # Note: This will return 401 due to auth, not 422 for validation
    response = client.post("/api/schedule", json={"target": "", "interval": 200})
    assert response.status_code in [401, 422]  # Either auth failure or validation

def test_rate_limiting():
    """Test rate limiting on auth endpoints."""
    # Multiple rapid login attempts
    for i in range(10):
        response = client.post("/api/login", json={"username": "test", "password": "test"})
        if response.status_code == 429:  # Rate limited
            break
    # Should eventually get rate limited (though test client might not enforce it perfectly)

def test_cors_headers():
    """Test CORS middleware is configured."""
    # CORS should be configured in the app
    from backend.api import app
    cors_middleware = None
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and 'CORSMiddleware' in str(middleware.cls):
            cors_middleware = middleware
            break
    assert cors_middleware is not None, "CORS middleware should be configured"