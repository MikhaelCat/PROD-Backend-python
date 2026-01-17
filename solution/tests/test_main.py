"""Tests for the main application endpoints"""

def test_ping_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}