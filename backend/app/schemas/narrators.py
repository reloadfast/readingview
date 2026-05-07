from pydantic import BaseModel


class NarratorBook(BaseModel):
    id: str
    title: str
    author: str
    duration: float
    duration_formatted: str
    is_finished: bool


class NarratorSummary(BaseModel):
    name: str
    book_count: int
    total_hours: float
    finished_count: int


class NarratorDetail(NarratorSummary):
    books: list[NarratorBook]
