from httpx import AsyncClient, ASGITransport
from app.main import app
import pytest

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_headers(client):
    response = await client.post("/login", data={"username": "default_user", "password": "123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
