from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class ReadingGoal(Base):
    __tablename__ = "reading_goals"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_books: Mapped[int] = mapped_column(Integer, nullable=False)
