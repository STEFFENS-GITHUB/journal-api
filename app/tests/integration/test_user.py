import pytest

@pytest.fixture
async def create_test_user(client, auth_headers):
    response = await client.post("/api/user/create", json={"username":"test_user", "password":"123"})
    assert response.status_code == 201
    user = response.json()
    yield user["id"]
    await client.delete(f"/api/user/{user['id']}", headers=auth_headers) # Uses default user creds to delete, rather then test user, will need changing

async def test_get_user(client, create_test_user):
    response = await client.get(f"/api/user/{create_test_user}")
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]
