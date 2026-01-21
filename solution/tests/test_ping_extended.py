"""Extended tests for ping endpoint with specific test names from the test suite"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    with TestClient(app) as c:
        yield c


def test_Ping(client):
    """Test the health check endpoint"""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}