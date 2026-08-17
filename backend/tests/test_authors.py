"""Tests for author discovery and following."""

from unittest.mock import AsyncMock, patch

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
