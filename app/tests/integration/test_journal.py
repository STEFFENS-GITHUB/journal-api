import pytest

@pytest.fixture
async def create_test_journal(client, auth_headers):
    response = await client.post("/api/journal/create",
                            json={"title":"Post Test Title", "body":"Post Test Body"},
                            headers=auth_headers)
    journal = response.json()
    yield journal["id"]
    await client.delete(f"/api/journal/{journal['id']}", headers=auth_headers)


async def test_create_journal(client, auth_headers):
    response = await client.post("/api/journal/create",
                            json={"title":"Post Test Title", "body":"Post Test Body"},
                            headers=auth_headers)
    assert response.status_code == 201
    journal = response.json()
    assert journal["title"] == "Post Test Title"
    assert journal["body"] == "Post Test Body"
    await client.delete(f"/api/journal/{journal['id']}", headers=auth_headers)

async def test_delete_journal(client, auth_headers, create_test_journal):
    response = await client.delete(f"/api/journal/{create_test_journal}", headers=auth_headers)
    assert response.status_code == 204

async def test_replace_journal(client, auth_headers, create_test_journal):
    response = await client.put(f"/api/journal/{create_test_journal}",
                            json={"title":"Update Test Title", "body":"Update Test Body"},
                            headers=auth_headers)
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Update Test Title"
    assert journal["body"] == "Update Test Body"

async def test_update_journal(client, auth_headers, create_test_journal):
    response = await client.patch(f"/api/journal/{create_test_journal}",
                            json={"body":"Patch Test Body"},
                            headers=auth_headers)
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Post Test Title"
    assert journal["body"] == "Patch Test Body"


    response = await client.patch(f"/api/journal/{create_test_journal}",
                            json={"title":"Patch Test Title"},
                            headers=auth_headers)
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Patch Test Title"
    assert journal["body"] == "Patch Test Body"

async def test_get_journals(client, auth_headers, create_test_journal):
    response = await client.get("/api/journal", headers=auth_headers)
    assert response.status_code == 200
    journal_ids = [journal["id"] for journal in response.json()]
    assert create_test_journal in journal_ids

async def test_get_journals_requires_auth(client):
    response = await client.get("/api/journal")
    assert response.status_code == 401

async def test_get_journal_index(client, create_test_journal):
    response = await client.get("/api/journal/index", params={"after_id": create_test_journal - 1})
    assert response.status_code == 200
    journals = response.json()
    assert len(journals) <= 50
    journal = journals[0]
    assert journal["id"] == create_test_journal
    assert journal["is_public"] is False
    assert journal["title"] == "Private"

async def test_get_journal(client, auth_headers, create_test_journal):
    response = await client.get(f"/api/journal/{create_test_journal}", headers=auth_headers)
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"]
    assert journal["body"]
