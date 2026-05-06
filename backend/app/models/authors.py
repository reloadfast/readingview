from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


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
