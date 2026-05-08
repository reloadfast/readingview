from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models.goals import ReadingGoal
from ..schemas.goals import ReadingGoalOut, ReadingGoalRequest

router = APIRouter()


@router.get("/goals", response_model=list[ReadingGoalOut])
async def list_goals(db: AsyncSession = Depends(get_db)) -> list[ReadingGoal]:
    async with db.begin():
        result = await db.execute(select(ReadingGoal).order_by(ReadingGoal.year.desc()))
    return list(result.scalars().all())


@router.put("/goals/{year}", response_model=ReadingGoalOut)
async def upsert_goal(
    year: int,
    body: ReadingGoalRequest,
    db: AsyncSession = Depends(get_db),
) -> ReadingGoal:
    async with db.begin():
        goal = await db.get(ReadingGoal, year)
        if goal is None:
            goal = ReadingGoal(year=year, target_books=body.target_books)
            db.add(goal)
        else:
            goal.target_books = body.target_books
    return goal
