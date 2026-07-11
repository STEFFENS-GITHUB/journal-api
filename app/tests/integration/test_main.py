from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.text

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}