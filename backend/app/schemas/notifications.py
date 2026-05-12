from pydantic import BaseModel


class NotificationResult(BaseModel):
    ok: bool
    error: str | None = None


class DigestReleaseItem(BaseModel):
    title: str
    author_name: str
    release_date: str | None


class DigestPreview(BaseModel):
    subject: str
    body: str
    count: int
    releases: list[DigestReleaseItem]
