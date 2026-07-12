from app.tests.integration.conftest import TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD

async def test_register(client):
    response = await client.post("/register", json={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 201
    user = response.json()
    assert user["username"] == TEST_USERNAME
    assert "password" not in user and "password_hash" not in user

    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    await client.delete(f"/api/user/{user['id']}", headers=headers)

async def test_register_duplicate_username(client, create_test_user):
    response = await client.post("/register", json={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 409

async def test_register_invalid_username(client):
    response = await client.post("/register", json={"username": "test user!", "email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 422

async def test_login(client, create_test_user):
    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"

async def test_login_wrong_password(client, create_test_user):
    response = await client.post("/login", data={"username": TEST_USERNAME, "password": "wrong-password"})
    assert response.status_code == 401

async def test_login_unknown_user(client):
    response = await client.post("/login", data={"username": "no-such-user", "password": "irrelevant"})
    assert response.status_code == 401
