import os

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.session import config_init
import pytest

@pytest.fixture
async def client():
    if os.getenv("DATABASE_URL_LOCAL"):
        os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_LOCAL"]
    app.state.engine, app.state.session_factory = config_init()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()

@pytest.fixture
async def auth_headers(client):
    response = await client.post("/login", data={
        "username": os.environ["DEFAULT_USER"],
        "password": os.environ["DEFAULT_USER_PASSWORD"],
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
