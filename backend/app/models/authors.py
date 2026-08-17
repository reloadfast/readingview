from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .releases import Release


class TrackedAuthor(Base):
    __tablename__ = "tracked_authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ol_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[str | None] = mapped_column(String, nullable=True)
    death_date: Mapped[str | None] = mapped_column(String, nullable=True)
    followed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # epoch ms
    releases: Mapped[list["Release"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
