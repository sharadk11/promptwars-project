import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search_invalid_radius():
    """Test validation error when radius is too large (Security & Input Validation)."""
    response = client.get("/search?location=Pune&radius=100")
    assert response.status_code == 422
    assert "Input should be less than or equal to 50.0" in response.text

def test_search_invalid_location_length():
    """Test validation error when location is too short (Security)."""
    response = client.get("/search?location=A")
    assert response.status_code == 422
    assert "String should have at least 2 characters" in response.text

def test_security_headers_present():
    """Test if our SecurityHeadersMiddleware successfully injects secure headers."""
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("strict-transport-security") == "max-age=31536000; includeSubDomains"
