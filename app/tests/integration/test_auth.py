from app.tests.integration.conftest import TEST_USERNAME, TEST_PASSWORD

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
