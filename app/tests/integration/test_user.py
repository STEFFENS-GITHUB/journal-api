async def test_get_user(client, create_test_user):
    user_id, headers = create_test_user
    response = await client.get(f"/api/user/{user_id}", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]
