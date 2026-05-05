from pydantic import BaseModel


class SeriesEntry(BaseModel):
    name: str
    sequence: str | None = None


class BookProgress(BaseModel):
    is_finished: bool
    progress_pct: float  # 0-100
    current_time: float  # seconds
    time_remaining: float  # seconds
    started_at: int | None = None  # epoch ms
    finished_at: int | None = None  # epoch ms
    last_update: int | None = None  # epoch ms


class LibraryBook(BaseModel):
    id: str
    title: str
    authors: str
    narrator: str | None = None
    series: list[SeriesEntry] = []
    cover_url: str
    duration: float
    genres: list[str] = []
    description: str | None = None
    published_year: str | None = None
    isbn: str | None = None
    asin: str | None = None
    progress: BookProgress | None = None
