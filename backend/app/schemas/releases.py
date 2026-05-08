from pydantic import BaseModel


class ReleaseTrackedAuthorOut(BaseModel):
    id: int
    name: str
    ol_key: str | None
    added_at: int

    class Config:
        from_attributes = True


class TrackAuthorRequest(BaseModel):
    name: str
    ol_key: str | None = None


class ReleaseOut(BaseModel):
    id: int
    title: str
    author_name: str
    release_date: str | None
    release_date_confirmed: bool
    book_number: str | None
    ol_key: str | None
    link_url: str | None
    notes: str | None
    source: str | None

    class Config:
        from_attributes = True


class PatchReleaseRequest(BaseModel):
    release_date_confirmed: bool | None = None
    release_date: str | None = None
    notes: str | None = None


class RefreshError(BaseModel):
    author: str
    message: str


class RefreshResult(BaseModel):
    added: int
    skipped: int
    failed: int = 0
    errors: list[RefreshError] = []
