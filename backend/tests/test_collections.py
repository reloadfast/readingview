"""Full CRUD tests for /api/collections."""


async def test_list_collections_empty(client):
    r = await client.get("/api/collections")
    assert r.status_code == 200
    assert r.json() == []


async def test_create_collection(client):
    r = await client.post(
        "/api/collections", json={"name": "Sci-Fi", "description": "My sci-fi picks"}
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Sci-Fi"
    assert data["description"] == "My sci-fi picks"
    assert data["book_count"] == 0
    assert "id" in data


async def test_create_duplicate_collection_returns_409(client):
    await client.post("/api/collections", json={"name": "Unique"})
    r = await client.post("/api/collections", json={"name": "Unique"})
    assert r.status_code == 409


async def test_list_collections_after_create(client):
    await client.post("/api/collections", json={"name": "Fantasy"})
    await client.post("/api/collections", json={"name": "Thriller"})
    r = await client.get("/api/collections")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "Fantasy" in names
    assert "Thriller" in names


async def test_get_collection_detail(client):
    create = await client.post("/api/collections", json={"name": "Horror"})
    coll_id = create.json()["id"]
    r = await client.get(f"/api/collections/{coll_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Horror"
    assert data["item_ids"] == []


async def test_get_collection_not_found(client):
    r = await client.get("/api/collections/99999")
    assert r.status_code == 404


async def test_patch_collection_name(client):
    create = await client.post("/api/collections", json={"name": "OldName"})
    coll_id = create.json()["id"]
    r = await client.patch(f"/api/collections/{coll_id}", json={"name": "NewName"})
    assert r.status_code == 200
    assert r.json()["name"] == "NewName"


async def test_patch_collection_not_found(client):
    r = await client.patch("/api/collections/99999", json={"name": "X"})
    assert r.status_code == 404


async def test_patch_collection_name_conflict(client):
    await client.post("/api/collections", json={"name": "Alpha"})
    b = await client.post("/api/collections", json={"name": "Beta"})
    beta_id = b.json()["id"]
    r = await client.patch(f"/api/collections/{beta_id}", json={"name": "Alpha"})
    assert r.status_code == 409


async def test_delete_collection(client):
    create = await client.post("/api/collections", json={"name": "ToDelete"})
    coll_id = create.json()["id"]
    r = await client.delete(f"/api/collections/{coll_id}")
    assert r.status_code == 204
    r2 = await client.get(f"/api/collections/{coll_id}")
    assert r2.status_code == 404


async def test_delete_collection_not_found(client):
    r = await client.delete("/api/collections/99999")
    assert r.status_code == 404


async def test_add_item_to_collection(client):
    create = await client.post("/api/collections", json={"name": "WithItems"})
    coll_id = create.json()["id"]
    r = await client.post(f"/api/collections/{coll_id}/items", json={"abs_item_id": "book-abc"})
    assert r.status_code == 201
    assert "book-abc" in r.json()["item_ids"]


async def test_add_duplicate_item_returns_409(client):
    create = await client.post("/api/collections", json={"name": "NoDupes"})
    coll_id = create.json()["id"]
    await client.post(f"/api/collections/{coll_id}/items", json={"abs_item_id": "book-x"})
    r = await client.post(f"/api/collections/{coll_id}/items", json={"abs_item_id": "book-x"})
    assert r.status_code == 409


async def test_add_item_collection_not_found(client):
    r = await client.post("/api/collections/99999/items", json={"abs_item_id": "book-y"})
    assert r.status_code == 404


async def test_remove_item_from_collection(client):
    create = await client.post("/api/collections", json={"name": "RemoveTest"})
    coll_id = create.json()["id"]
    await client.post(f"/api/collections/{coll_id}/items", json={"abs_item_id": "book-z"})
    r = await client.delete(f"/api/collections/{coll_id}/items/book-z")
    assert r.status_code == 204


async def test_remove_item_not_found(client):
    create = await client.post("/api/collections", json={"name": "EmptyCol"})
    coll_id = create.json()["id"]
    r = await client.delete(f"/api/collections/{coll_id}/items/nonexistent")
    assert r.status_code == 404
