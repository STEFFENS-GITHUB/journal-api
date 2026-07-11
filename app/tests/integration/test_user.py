import pytest

@pytest.fixture
async def create_test_user(client):
    response = await client.post("/api/user/create", json={"username":"test_user", "password":"123"})
    user = response.json()
    response = await client.post("/login", data={"username":"test_user", "password":"123"})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    yield user["id"], headers
    await client.delete(f"/api/user/{user['id']}", headers=headers)

async def test_get_user(client, create_test_user):
    user_id, headers = create_test_user
    response = await client.get(f"/api/user/{user_id}", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]
