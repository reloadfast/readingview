from pydantic import BaseModel, Field


class ReadingGoalOut(BaseModel):
    year: int
    target_books: int


class ReadingGoalRequest(BaseModel):
    target_books: int = Field(gt=0)
