from pydantic import BaseModel


class SeriesBook(BaseModel):
    id: str
    title: str
    author: str
    sequence: str
    is_finished: bool
    progress: float
    duration: float
    duration_formatted: str


class SeriesSummary(BaseModel):
    name: str
    author: str
    total: int
    finished: int
    in_progress: int
    not_started: int
    percent_complete: float


class SeriesDetail(SeriesSummary):
    books: list[SeriesBook]
