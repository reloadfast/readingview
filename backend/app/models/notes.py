from sqlalchemy import Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class BookNote(Base):
    __tablename__ = "book_notes"

    abs_item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)
