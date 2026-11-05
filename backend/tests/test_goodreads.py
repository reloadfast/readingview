"""Synthetic metadata fixtures: these are not captures of live Goodreads pages."""

import json

import httpx
import pytest

from app.services.goodreads import MAX_BYTES, canonical_url, parse_page, probe

URL = "https://www.goodreads.com/book/show/257149406-bog-standard-isekai"
CANONICAL = "https://www.goodreads.com/book/show/257149406"


def script(value, *, next_data=False):
    attribute = 'id="__NEXT_DATA__"' if next_data else 'type="application/ld+json"'
    return f"<script {attribute}>{json.dumps(value)}</script>"


def test_json_ld_maps_existing_fields_without_guessing_series_or_audio():
    html = script(
        {
            "@context": "https://schema.org",
            "@type": "Book",
            "url": URL,
            "name": "Sample & Title",
            "author": [{"@type": "Person", "name": "Sample Author"}],
            "datePublished": "2027-08-17",
            "bookFormat": "https://schema.org/EBook",
            "image": {"url": "https://example.org/cover.jpg"},
        }
    )
    result = parse_page(html, URL)
    assert result["fields"] == {
        "title": "Sample & Title",
        "author": "Sample Author",
        "series": None,
        "series_number": None,
        "release_date": "2027-08-17",
        "media": ["ebook"],
        "cover_url": "https://example.org/cover.jpg",
        "link_url": CANONICAL,
        "status": "watching",
    }
    assert result["status"] == "partial"
    assert result["missing_fields"] == ["series", "series_number"]
    assert any("work rather than this edition" in warning for warning in result["warnings"])


def test_next_data_selects_requested_book_and_resolves_author_and_series():
    html = script({"@type": "Book", "name": "Generic title", "datePublished": "2024"})
    html += script(
        {
            "props": {
                "pageProps": {
                    "apolloState": {
                        "Book:other": {
                            "__typename": "Book",
                            "legacyId": 123,
                            "title": "Recommendation",
                        },
                        "Book:target": {
                            "__typename": "Book",
                            "legacyId": 257149406,
                            "title": "Sample title",
                            "imageUrl": "https://example.org/cover.jpg",
                            "primaryContributorEdge": {"node": {"__ref": "Contributor:1"}},
                            "details": {
                                "publicationTime": 1818460800000,
                                "bookFormat": "Audible Audio",
                            },
                            "bookSeries": [{"series": {"__ref": "Series:1"}, "userPosition": "6"}],
                        },
                        "Contributor:1": {"name": "Sample Author"},
                        "Series:1": {"title": "Sample Series"},
                    }
                }
            }
        },
        next_data=True,
    )
    result = parse_page(html, URL)
    assert result["status"] == "ok"
    assert result["fields"]["title"] == "Sample title"
    assert result["fields"]["author"] == "Sample Author"
    assert result["fields"]["series"] == "Sample Series"
    assert result["fields"]["series_number"] == 6
    assert result["fields"]["media"] == ["audiobook"]
    assert result["fields"]["release_date"] == "2027-08-17"
    assert result["sources"]["release_date"] == "next_data"


def test_ambiguous_json_ld_does_not_import_recommended_book():
    html = script(
        {
            "@graph": [
                {"@type": "Book", "name": "Other book"},
                {"@type": "Book", "name": "Another book"},
            ]
        }
    )
    assert parse_page(html, URL)["fields"]["title"] is None


def test_explicitly_different_book_is_not_imported():
    html = script({"@type": "Book", "name": "Other book", "url": "/book/show/123"})
    assert parse_page(html, URL)["fields"]["title"] is None


@pytest.mark.parametrize("publication", ["2027-02-30", "August 2027", None])
def test_unknown_dates_remain_empty(publication):
    result = parse_page(
        script({"@type": "Book", "name": "Sample", "datePublished": publication}), URL
    )
    assert result["fields"]["release_date"] is None


def test_bad_json_can_fall_back_to_open_graph_without_inventing_fields():
    html = '<script type="application/ld+json">broken</script>'
    html += '<meta property="og:title" content="Sample &amp; Title">'
    result = parse_page(html, URL)
    assert result["fields"]["title"] == "Sample & Title"
    assert result["fields"]["author"] is None
    assert result["sources"]["title"] == "open_graph"


@pytest.mark.parametrize(
    "url",
    [
        "http://www.goodreads.com/book/show/123",
        "https://goodreads.com.evil.test/book/show/123",
        "https://localhost/book/show/123",
        "https://www.goodreads.com/api",
        "https://user:secret@www.goodreads.com/book/show/123",
        "https://www.goodreads.com:8004/book/show/123",
    ],
)
def test_url_restrictions(url):
    with pytest.raises(ValueError):
        canonical_url(url)


def test_tracking_parameters_are_removed():
    assert canonical_url(URL + "?from_search=true#reviews") == CANONICAL


def test_challenge_open_graph_title_is_not_usable_book_metadata():
    html = '<meta property="og:title" content="Verify you are human">'
    html += "In order to continue, we need to verify that you're not a robot."
    result = parse_page(html, URL)
    assert result["status"] == "blocked"
    assert result["fields"]["title"] is None


@pytest.mark.parametrize("status", [200, 202, 403, 429])
async def test_bot_challenge_is_reported_even_with_success_status(status):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status, text="In order to continue, we need to verify that you're not a robot."
        )
    )
    result = await probe(URL, transport=transport)
    assert result["status"] == "blocked"
    assert result["http_status"] == status
    assert result["fields"]["title"] is None


async def test_slug_redirect_is_followed_without_looping():
    requests = []

    def handler(request):
        requests.append(str(request.url))
        if str(request.url) == CANONICAL:
            return httpx.Response(302, headers={"location": URL})
        return httpx.Response(200, text=script({"@type": "Book", "name": "Sample"}))

    assert (await probe(URL, transport=httpx.MockTransport(handler)))["status"] == "partial"
    assert requests == [CANONICAL, URL]


@pytest.mark.parametrize(
    "target", ["http://192.168.1.110:8004/", "/user/sign_in", "/book/show/999"]
)
async def test_disallowed_redirect_is_not_fetched(target):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={"location": target})

    assert (await probe(URL, transport=httpx.MockTransport(handler)))["status"] == "blocked"
    assert len(requests) == 1


async def test_oversized_response_is_rejected():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * (MAX_BYTES + 1))
    )
    assert (await probe(URL, transport=transport))["status"] == "too_large"


async def test_network_error_does_not_print_potential_credentials():
    def handler(request):
        raise httpx.ConnectError("proxy://user:secret@proxy.test", request=request)

    result = await probe(URL, transport=httpx.MockTransport(handler))
    assert result == {"status": "network_error", "url": CANONICAL, "error_type": "ConnectError"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"primaryContributorEdge": "invalid"},
        {"primaryContributorEdge": {"node": {"__ref": ["invalid"]}}},
        {"details": ["invalid"]},
        {"bookSeries": 42},
        {"bookSeries": ["invalid"]},
        {"bookSeries": [{"series": {"__ref": "missing"}, "userPosition": True}]},
        {"bookSeries": [{"series": None, "userPosition": "Infinity"}]},
    ],
)
def test_malformed_next_fields_do_not_crash_or_invent_metadata(overrides):
    book = {"__typename": "Book", "legacyId": 257149406, "title": "Sample", **overrides}
    html = script({"props": {"pageProps": {"apolloState": {"Book:target": book}}}}, next_data=True)
    result = parse_page(html, URL)
    assert result["status"] == "partial"
    assert result["fields"]["title"] == "Sample"
    assert result["fields"]["author"] is None
    assert result["fields"]["series_number"] is None
