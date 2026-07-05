import os

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
    response = await client.post("/login", data={
        "username": os.environ["DEFAULT_USER"],
        "password": os.environ["DEFAULT_USER_PASSWORD"],
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
