"""Unit tests for pure functions in services/narrators.py."""
import pytest

from app.services.narrators import compute_narrator_detail, compute_narrator_list

pytestmark = pytest.mark.unit


def _make_item(
    item_id: str,
    narrator: str,
    title: str = "A Book",
    author: str = "Author",
    duration: float = 3600.0,
) -> dict:
    return {
        "id": item_id,
        "media": {
            "duration": duration,
            "metadata": {
                "narratorName": narrator,
                "title": title,
                "authorName": author,
            },
        },
    }


_ITEMS = [
    _make_item("b1", "Alice Reader", "Book One", duration=3600.0),
    _make_item("b2", "Alice Reader", "Book Two", duration=7200.0),
    _make_item("b3", "Bob Narrator", "Book Three", duration=5400.0),
    _make_item("b4", "Alice Reader, Bob Narrator", "Book Four", duration=1800.0),
    _make_item("b5", "", "No Narrator Book"),  # should be skipped
]

_PROGRESS = {
    "b1": {"isFinished": True, "progress": 1.0},
    "b2": {"isFinished": False, "progress": 0.5},
}


def test_compute_narrator_list_names():
    result = compute_narrator_list(_ITEMS, {})
    names = [n.name for n in result]
    assert "Alice Reader" in names
    assert "Bob Narrator" in names


def test_compute_narrator_list_excludes_empty_narrator():
    result = compute_narrator_list(_ITEMS, {})
    names = [n.name for n in result]
    assert "" not in names


def test_compute_narrator_list_multi_narrator_split():
    result = compute_narrator_list(_ITEMS, {})
    alice = next(n for n in result if n.name == "Alice Reader")
    bob = next(n for n in result if n.name == "Bob Narrator")
    # Book Four has both Alice and Bob — each should have it counted
    assert alice.book_count == 3  # b1, b2, b4
    assert bob.book_count == 2   # b3, b4


def test_compute_narrator_list_total_hours():
    result = compute_narrator_list(_ITEMS, {})
    alice = next(n for n in result if n.name == "Alice Reader")
    expected_hours = (3600 + 7200 + 1800) / 3600
    assert alice.total_hours == pytest.approx(expected_hours, rel=1e-2)


def test_compute_narrator_list_finished_count():
    result = compute_narrator_list(_ITEMS, _PROGRESS)
    alice = next(n for n in result if n.name == "Alice Reader")
    assert alice.finished_count == 1  # only b1 is finished


def test_compute_narrator_list_sorted_by_name():
    result = compute_narrator_list(_ITEMS, {})
    names = [n.name for n in result]
    assert names == sorted(names, key=str.lower)


def test_compute_narrator_list_empty():
    assert compute_narrator_list([], {}) == []


def test_compute_narrator_detail_found():
    detail = compute_narrator_detail("Alice Reader", _ITEMS, _PROGRESS)
    assert detail is not None
    assert detail.name == "Alice Reader"
    assert detail.book_count == 3
    assert detail.finished_count == 1


def test_compute_narrator_detail_books_sorted_by_title():
    detail = compute_narrator_detail("Alice Reader", _ITEMS, {})
    assert detail is not None
    titles = [b.title for b in detail.books]
    assert titles == sorted(titles, key=str.lower)


def test_compute_narrator_detail_not_found():
    assert compute_narrator_detail("Unknown Narrator", _ITEMS, {}) is None
