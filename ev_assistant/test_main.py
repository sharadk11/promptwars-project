import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    """Test the root UI endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "EV Station Finder" in response.text

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "EV Assistant"}

def test_search_missing_location():
    """Test the search endpoint with missing required parameters."""
    response = client.get("/search")
    assert response.status_code == 422 # Unprocessable Entity
