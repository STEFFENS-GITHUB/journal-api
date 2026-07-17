from app.utils.utils import create_access_token, create_email_verification_token
from app.tests.integration.conftest import TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD

async def test_register(client):
    response = await client.post("/register", json={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 201
    user = response.json()
    assert user["username"] == TEST_USERNAME
    assert "password" not in user and "password_hash" not in user

    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert response.status_code == 403

    token = create_email_verification_token(user["id"])
    response = await client.get(f"/verify-email?token={token}")
    assert response.status_code == 200

    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    await client.delete(f"/api/user/{user['id']}", headers=headers)

async def test_verify_email_invalid_token(client):
    response = await client.get("/verify-email?token=not-a-real-token")
    assert response.status_code == 400

async def test_verify_email_rejects_login_token(client):
    login_token = create_access_token(user_id=1)
    response = await client.get(f"/verify-email?token={login_token}")
    assert response.status_code == 400
    
async def test_register_duplicate_username(client, create_test_user):
    response = await client.post("/register", json={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 409

async def test_register_duplicate_email(client, create_test_user):
    response = await client.post("/register", json={"username": "other_user", "email": TEST_EMAIL, "password": TEST_PASSWORD})
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

async def test_login_with_email(client, create_test_user):
    response = await client.post("/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
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

async def test_refresh_token_rotation(client, create_test_user):
    user_id, _ = create_test_user
    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    old_refresh = response.json()["refresh_token"]

    response = await client.post("/refresh-token", json={"refresh_token": old_refresh})
    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != old_refresh

    response = await client.get(f"/api/user/{user_id}", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert response.status_code == 200

    response = await client.post("/refresh-token", json={"refresh_token": old_refresh})
    assert response.status_code == 401

    response = await client.post("/refresh-token", json={"refresh_token": body["refresh_token"]})
    assert response.status_code == 401

async def test_refresh_token_invalid(client):
    response = await client.post("/refresh-token", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401

async def test_logout_revokes_refresh_token(client, create_test_user):
    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    refresh_token = response.json()["refresh_token"]

    response = await client.post("/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204

    response = await client.post("/refresh-token", json={"refresh_token": refresh_token})
    assert response.status_code == 401
