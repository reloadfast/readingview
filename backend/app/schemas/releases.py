from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _validate_release_date(value: str | None) -> str | None:
    """Accept only a calendar year or an ISO calendar date."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) == 4 and value.isdigit():
        return value
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("release_date must use YYYY or YYYY-MM-DD") from exc


class ReleaseTrackedAuthorOut(BaseModel):
    """Legacy response shape retained for generated client compatibility."""

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
    is_active: bool

    class Config:
        from_attributes = True


class PatchReleaseRequest(BaseModel):
    release_date_confirmed: bool | None = None
    release_date: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    _validate_date = field_validator("release_date")(_validate_release_date)


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
    series_number: float | None = None
    release_date: str | None = None
    media: list[ManualReleaseMedium] = Field(default_factory=list)
    cover_url: str | None = None
    link_url: str | None = None
    comments: str | None = None
    last_checked_at: int | None = None
    status: ManualReleaseStatus = "watching"

    _validate_date = field_validator("release_date")(_validate_release_date)


class ManualReleasePatch(ManualReleaseCreate):
    archived: bool | None = None


class ManualReleaseOut(BaseModel):
    id: int
    author: str | None
    title: str | None
    series: str | None
    series_number: float | None
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
