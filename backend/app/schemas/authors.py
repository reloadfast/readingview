from pydantic import BaseModel


class AuthorBook(BaseModel):
    id: str
    title: str
    narrator: str
    duration: float
    duration_formatted: str
    is_finished: bool


class AuthorDetail(BaseModel):
    name: str
    book_count: int
    total_hours: float
    finished_count: int
    books: list[AuthorBook]


class TrackedAuthorOut(BaseModel):
    id: int
    name: str
    ol_key: str | None
    photo_url: str | None
    bio: str | None
    birth_date: str | None
    death_date: str | None
    followed_at: int  # epoch ms

    model_config = {"from_attributes": True}


class LibraryAuthor(BaseModel):
    name: str
    book_count: int


class OLAuthorResult(BaseModel):
    ol_key: str
    name: str
    birth_date: str | None = None
    death_date: str | None = None
    photo_url: str | None = None
    top_work: str | None = None
    work_count: int = 0


class FollowRequest(BaseModel):
    name: str
    ol_key: str | None = None
