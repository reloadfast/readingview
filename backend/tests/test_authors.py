"""Tests for author discovery and following."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.api import authors as authors_api


def test_extract_abs_authors_uses_authors_list_and_author_name():
    authors = authors_api._extract_abs_authors(
        [
            {"media": {"metadata": {"authors": [{"name": "Ada Lovelace"}]}}},
            {"media": {"metadata": {"authorName": "Ada Lovelace, Grace Hopper"}}},
        ]
    )

    assert [(author.name, author.book_count) for author in authors] == [
        ("Ada Lovelace", 2),
        ("Grace Hopper", 1),
    ]


async def test_follow_author_succeeds_when_optional_detail_lookup_fails(client):
    with patch.object(
        authors_api._OL,
        "get_author_details",
        new=AsyncMock(side_effect=httpx.ConnectError("Open Library unavailable")),
    ):
        response = await client.post(
            "/api/authors",
            json={"name": "J. Zachary Pike", "ol_key": "OL7639117A"},
        )

    assert response.status_code == 201
    assert response.json()["name"] == "J. Zachary Pike"
    assert response.json()["ol_key"] == "OL7639117A"


async def test_follow_library_author_succeeds_when_search_fails(client):
    with patch.object(
        authors_api._OL,
        "search_authors",
        new=AsyncMock(side_effect=httpx.ConnectError("Open Library unavailable")),
    ):
        response = await client.post("/api/authors", json={"name": "Katherine Addison"})

    assert response.status_code == 201
    assert response.json()["name"] == "Katherine Addison"
    assert response.json()["ol_key"] is None


async def test_followed_author_photo_is_served_from_local_cache(client):
    with patch.object(
        authors_api._OL,
        "get_author_details",
        new=AsyncMock(return_value={"key": "/authors/OL7639117A", "photos": [123]}),
    ):
        followed = await client.post(
            "/api/authors", json={"name": "J. Zachary Pike", "ol_key": "OL7639117A"}
        )

    cache = MagicMock()
    cache.get = AsyncMock(return_value=b"cached-photo")
    with patch.object(authors_api, "get_cover_cache", return_value=cache):
        with patch("app.api.authors.httpx.AsyncClient") as http_client:
            photo = await client.get(followed.json()["photo_url"])

    assert followed.status_code == 201
    assert followed.json()["photo_url"] == f"/api/authors/{followed.json()['id']}/photo"
    assert photo.status_code == 200
    assert photo.content == b"cached-photo"
    cache.get.assert_awaited_once()
    http_client.assert_not_called()
