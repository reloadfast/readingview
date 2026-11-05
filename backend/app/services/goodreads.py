"""Read-only Goodreads book metadata lookup, independent of API and CLI code."""

import json
import math
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import Literal, NotRequired, TypedDict, cast
from urllib.parse import urljoin, urlsplit

import httpx

MAX_BYTES = 5 * 1024 * 1024
MetadataField = Literal[
    "title", "author", "series", "series_number", "release_date", "media", "cover_url"
]
MetadataSource = Literal["json_ld", "next_data", "open_graph"]
Medium = Literal["audiobook", "ebook", "hardcover", "paperback"]
MetadataValue = str | float | list[Medium] | None
LookupStatus = Literal[
    "ok", "partial", "blocked", "no_metadata", "too_large", "http_error", "network_error"
]
FIELDS: tuple[MetadataField, ...] = (
    "title",
    "author",
    "series",
    "series_number",
    "release_date",
    "media",
    "cover_url",
)


class GoodreadsFields(TypedDict):
    title: str | None
    author: str | None
    series: str | None
    series_number: float | None
    release_date: str | None
    media: list[Medium] | None
    cover_url: str | None
    link_url: str
    status: Literal["watching"]


class GoodreadsResult(TypedDict):
    """Lookup diagnostics; metadata is present only when a page was parsed.

    Failed fetches may omit metadata entirely. Consumers must check status before
    using fields. Null media retains the diagnostic CLI's existing representation;
    an eventual API adapter can normalize it to the create contract's empty list.
    """

    status: LookupStatus
    url: str
    fields: NotRequired[GoodreadsFields]
    sources: NotRequired[dict[MetadataField, MetadataSource]]
    missing_fields: NotRequired[list[MetadataField]]
    detected_data: NotRequired[list[MetadataSource]]
    warnings: NotRequired[list[str]]
    http_status: NotRequired[int]
    bytes_received: NotRequired[int]
    message: NotRequired[str]
    error_type: NotRequired[str]


def _mapping(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return cast(list[object], value) if isinstance(value, list) else []


def _resolve(value: object, cache: dict[str, object]) -> dict[str, object]:
    node = _mapping(value)
    reference = node.get("__ref")
    return _mapping(cache.get(reference)) if isinstance(reference, str) else node


def canonical_url(value: str) -> str:
    """Accept public HTTPS book links only; strip tracking parameters."""
    parts = urlsplit(value.strip())
    book_path = re.fullmatch(r"/book/show/([0-9]+)(?:[-.][^/]+)?/?", parts.path)
    if (
        parts.scheme != "https"
        or parts.hostname not in {"goodreads.com", "www.goodreads.com"}
        or parts.username is not None
        or parts.password is not None
        or parts.port not in {None, 443}
        or book_path is None
    ):
        raise ValueError("Use an HTTPS Goodreads /book/show/<id> URL.")
    return f"https://www.goodreads.com/book/show/{book_path[1]}"


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.documents: list[tuple[MetadataSource, object]] = []
        self.meta: dict[str, str] = {}
        self._script: MetadataSource | None = None
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            if key and attributes.get("content"):
                self.meta[key] = attributes["content"] or ""
        if tag == "script":
            self._script = (
                "json_ld"
                if attributes.get("type") == "application/ld+json"
                else "next_data"
                if attributes.get("id") == "__NEXT_DATA__"
                else None
            )
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._script:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script:
            try:
                self.documents.append((self._script, json.loads("".join(self._chunks))))
            except (ValueError, RecursionError):
                pass
            self._script = None
            self._chunks = []


def _objects(value: object) -> Iterator[dict[str, object]]:
    pending = [value]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            yield _mapping(node)
            pending.extend(reversed(list(node.values())))
        elif isinstance(node, list):
            pending.extend(reversed(node))


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _date(value: object) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value / 1000, UTC).date().isoformat()
        except (ValueError, OverflowError, OSError):
            return None
    text = _text(value)
    if text and re.fullmatch(r"[0-9]{4}", text):
        return text if 1 <= int(text) <= 9999 else None
    if text and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T.*)?", text):
        try:
            return date.fromisoformat(text[:10]).isoformat()
        except ValueError:
            pass
    return None


def _medium(value: object) -> list[Medium] | None:
    text = (_text(value) or "").rsplit("/", 1)[-1].lower()
    formats: dict[str, list[Medium]] = {
        "audiobook": ["audiobook"],
        "audiobookformat": ["audiobook"],
        "audible audio": ["audiobook"],
        "ebook": ["ebook"],
        "kindle edition": ["ebook"],
        "hardcover": ["hardcover"],
        "paperback": ["paperback"],
    }
    return formats.get(text)


def parse_page(html: str, url: str) -> GoodreadsResult:
    url = canonical_url(url)
    page = _Page()
    page.feed(html)
    values: dict[MetadataField, MetadataValue] = {field: None for field in FIELDS}
    sources: dict[MetadataField, MetadataSource] = {}
    warnings = ["Review the edition, date and medium before saving; no audiobook date is inferred."]

    def put(field: MetadataField, value: MetadataValue, source: MetadataSource) -> None:
        if value is not None and values[field] is None:
            values[field] = value
            sources[field] = source

    book_id = url.rsplit("/", 1)[-1]
    # Edition-specific Next data takes precedence over generic JSON-LD dates.
    for kind, document in sorted(page.documents, key=lambda item: item[0] != "next_data"):
        objects = list(_objects(document))
        if kind == "next_data":
            # Apollo cache entries refer to author/series objects by __ref.
            cache = next(
                (
                    _mapping(node["apolloState"])
                    for node in objects
                    if isinstance(node.get("apolloState"), dict)
                ),
                {},
            )

            books = [
                node
                for node in objects
                if node.get("__typename") == "Book" and str(node.get("legacyId")) == book_id
            ]
            for book in books:
                put("title", _text(book.get("title")), kind)
                put("cover_url", _text(book.get("imageUrl")), kind)
                edge = _resolve(book.get("primaryContributorEdge"), cache)
                author = _resolve(edge.get("node"), cache)
                put("author", _text(author.get("name")), kind)
                details = _resolve(book.get("details"), cache)
                put("release_date", _date(details.get("publicationTime")), kind)
                put("media", _medium(details.get("bookFormat")), kind)
                for raw_entry in _list(book.get("bookSeries")):
                    entry = _resolve(raw_entry, cache)
                    series = _resolve(entry.get("series"), cache)
                    put("series", _text(series.get("title")), kind)
                    try:
                        position = entry.get("userPosition")
                        number = (
                            float(position) if isinstance(position, (str, int, float)) else None
                        )
                        if (
                            number is not None
                            and not isinstance(position, bool)
                            and math.isfinite(number)
                        ):
                            put("series_number", number, kind)
                    except (TypeError, ValueError, OverflowError):
                        pass
                    break
        else:
            books = [
                node
                for node in objects
                if "Book"
                in (
                    _list(node.get("@type"))
                    if isinstance(node.get("@type"), list)
                    else [node.get("@type")]
                )
            ]
            matches = [
                node
                for node in books
                if re.search(
                    rf"/book/show/{book_id}(?:\D|$)", str(node.get("url") or node.get("@id") or "")
                )
            ]
            unlinked_single = (
                books
                if len(books) == 1 and not (books[0].get("url") or books[0].get("@id"))
                else []
            )
            for book in matches or unlinked_single:
                put("title", _text(book.get("name")), kind)
                authors = book.get("author") or []
                authors = authors if isinstance(authors, list) else [authors]
                names = [
                    name
                    for author in authors
                    if (name := _text(author.get("name") if isinstance(author, dict) else author))
                ]
                put("author", ", ".join(names) or None, kind)
                image = book.get("image")
                put(
                    "cover_url", _text(image.get("url") if isinstance(image, dict) else image), kind
                )
                put("release_date", _date(book.get("datePublished")), kind)
                put("media", _medium(book.get("bookFormat")), kind)

    put("title", _text(page.meta.get("og:title")), "open_graph")
    put("cover_url", _text(page.meta.get("og:image")), "open_graph")
    challenge = any(
        marker in html.lower()
        for marker in (
            "verify that you're not a robot",
            "captcha",
            "automated access",
            "cf-chl-",
        )
    )
    if challenge and sources.get("title") == "open_graph":
        # Verification pages can supply their own Open Graph metadata.
        values["title"] = None
        sources.pop("title", None)
    status: LookupStatus = "ok" if all(values[field] is not None for field in FIELDS) else "partial"
    if values["title"] is None:
        status = "blocked" if challenge else "no_metadata"
    if challenge:
        warnings.append("Bot-verification markers detected; metadata may be unavailable.")
    if sources.get("release_date") == "json_ld":
        warnings.append("JSON-LD publication date may describe the work rather than this edition.")
    return {
        "status": status,
        "url": url,
        # The builder accepts a field/value union; extraction above supplies the
        # corresponding type for each field before this single report boundary.
        "fields": cast(GoodreadsFields, {**values, "link_url": url, "status": "watching"}),
        "sources": sources,
        "missing_fields": [field for field in FIELDS if values[field] is None],
        "detected_data": sorted({kind for kind, _ in page.documents}),
        "warnings": warnings,
    }


async def probe(url: str, *, transport: httpx.AsyncBaseTransport | None = None) -> GoodreadsResult:
    url = canonical_url(url)
    current = url
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=False,
        transport=transport,
        headers={
            "User-Agent": "ReadingView/1.0 (Goodreads metadata access prototype)",
            "Accept": "text/html",
        },
    ) as client:
        try:
            for _ in range(4):
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        try:
                            target = urljoin(current, response.headers["location"])
                            target_book = canonical_url(target)
                        except (ValueError, KeyError):
                            return {
                                "status": "blocked",
                                "url": url,
                                "message": "Redirect left the allowed Goodreads book URLs.",
                            }
                        if target_book != url:
                            return {
                                "status": "blocked",
                                "url": url,
                                "message": "Redirect changed the requested book ID.",
                            }
                        current = urlsplit(target)._replace(query="", fragment="").geturl()
                        continue
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_BYTES:
                            return {"status": "too_large", "url": url}
                    result = parse_page(
                        content.decode(response.encoding or "utf-8", errors="replace"), url
                    )
                    result["http_status"] = response.status_code
                    result["bytes_received"] = len(content)
                    if response.status_code >= 400:
                        result["status"] = (
                            "blocked" if response.status_code in {403, 429} else "http_error"
                        )
                    return result
            return {"status": "blocked", "url": url, "message": "Too many redirects."}
        except httpx.HTTPError as exc:
            # Exception strings can contain proxy credentials; report only their class.
            return {"status": "network_error", "url": url, "error_type": type(exc).__name__}
