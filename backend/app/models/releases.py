from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class ReleaseTrackedAuthor(Base):
    __tablename__ = "release_tracked_authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ol_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    added_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # epoch ms

    releases: Mapped[list["Release"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("release_tracked_authors.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    release_date: Mapped[str | None] = mapped_column(String, nullable=True)
    release_date_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    book_number: Mapped[str | None] = mapped_column(String, nullable=True)
    ol_key: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    link_url: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    author: Mapped["ReleaseTrackedAuthor"] = relationship(back_populates="releases")


class ManualRelease(Base):
    """A locally-maintained release record, independent of Open Library refreshes."""

    __tablename__ = "manual_releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    series: Mapped[str | None] = mapped_column(String, nullable=True)
    series_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    release_date: Mapped[str | None] = mapped_column(String, nullable=True)
    media: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    link_url: Mapped[str | None] = mapped_column(String, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="watching")
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # SHA-256 of normalized author/title/date/media. This is the duplicate boundary.
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
