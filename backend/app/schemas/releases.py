from typing import Literal

from pydantic import BaseModel, Field


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


ManualReleaseStatus = Literal["watching", "released", "owned"]
ManualReleaseMedium = Literal["audiobook", "ebook", "hardcover", "paperback"]


class ManualReleaseCreate(BaseModel):
    author: str | None = None
    title: str | None = None
    series: str | None = None
    release_date: str | None = None
    media: list[ManualReleaseMedium] = Field(default_factory=list)
    cover_url: str | None = None
    link_url: str | None = None
    comments: str | None = None
    last_checked_at: int | None = None
    status: ManualReleaseStatus = "watching"


class ManualReleasePatch(ManualReleaseCreate):
    archived: bool | None = None


class ManualReleaseOut(BaseModel):
    id: int
    author: str | None
    title: str | None
    series: str | None
    release_date: str | None
    media: list[ManualReleaseMedium]
    cover_url: str | None
    uploaded_cover_url: str | None
    link_url: str | None
    comments: str | None
    last_checked_at: int | None
    updated_at: int
    status: ManualReleaseStatus
    archived: bool
