from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models.collections import Collection, CollectionItem
from ..schemas.collections import (
    AddItemRequest,
    CollectionDetail,
    CollectionOut,
    CreateCollectionRequest,
    PatchCollectionRequest,
)

router = APIRouter()


def _to_out(coll: Collection) -> CollectionOut:
    return CollectionOut(
        id=coll.id,
        name=coll.name,
        description=coll.description,
        created_at=coll.created_at,
        book_count=len(coll.items),
    )


def _to_detail(coll: Collection) -> CollectionDetail:
    return CollectionDetail(
        id=coll.id,
        name=coll.name,
        description=coll.description,
        created_at=coll.created_at,
        book_count=len(coll.items),
        item_ids=[ci.abs_item_id for ci in coll.items],
    )


@router.get("/collections", response_model=list[CollectionOut])
async def list_collections(db: AsyncSession = Depends(get_db)) -> list[CollectionOut]:
    async with db.begin():
        rows = (
            await db.execute(select(Collection).order_by(Collection.name))
        ).scalars().all()
    return [_to_out(c) for c in rows]


@router.post("/collections", response_model=CollectionOut, status_code=201)
async def create_collection(
    body: CreateCollectionRequest,
    db: AsyncSession = Depends(get_db),
) -> CollectionOut:
    async with db.begin():
        existing = (
            await db.execute(select(Collection).where(Collection.name == body.name))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Collection name already exists")

        coll = Collection(
            name=body.name,
            description=body.description,
            created_at=datetime.now(timezone.utc).date().isoformat(),
        )
        db.add(coll)

    await db.refresh(coll, ["items"])
    return _to_out(coll)


@router.get("/collections/{collection_id}", response_model=CollectionDetail)
async def get_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
) -> CollectionDetail:
    async with db.begin():
        coll = (
            await db.execute(
                select(Collection).where(Collection.id == collection_id)
            )
        ).scalar_one_or_none()
        if coll is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        return _to_detail(coll)


@router.patch("/collections/{collection_id}", response_model=CollectionOut)
async def patch_collection(
    collection_id: int,
    body: PatchCollectionRequest,
    db: AsyncSession = Depends(get_db),
) -> CollectionOut:
    async with db.begin():
        coll = (
            await db.execute(
                select(Collection).where(Collection.id == collection_id)
            )
        ).scalar_one_or_none()
        if coll is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        if body.name is not None:
            name_conflict = (
                await db.execute(
                    select(Collection).where(
                        Collection.name == body.name,
                        Collection.id != collection_id,
                    )
                )
            ).scalar_one_or_none()
            if name_conflict:
                raise HTTPException(status_code=409, detail="Collection name already exists")
            coll.name = body.name

        if body.description is not None:
            coll.description = body.description or None

        return _to_out(coll)


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin():
        coll = (
            await db.execute(
                select(Collection).where(Collection.id == collection_id)
            )
        ).scalar_one_or_none()
        if coll is None:
            raise HTTPException(status_code=404, detail="Collection not found")
        await db.delete(coll)


@router.post("/collections/{collection_id}/items", response_model=CollectionDetail, status_code=201)
async def add_item(
    collection_id: int,
    body: AddItemRequest,
    db: AsyncSession = Depends(get_db),
) -> CollectionDetail:
    async with db.begin():
        coll = (
            await db.execute(
                select(Collection).where(Collection.id == collection_id)
            )
        ).scalar_one_or_none()
        if coll is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        already = (
            await db.execute(
                select(CollectionItem).where(
                    CollectionItem.collection_id == collection_id,
                    CollectionItem.abs_item_id == body.abs_item_id,
                )
            )
        ).scalar_one_or_none()
        if already:
            raise HTTPException(status_code=409, detail="Item already in collection")

        db.add(CollectionItem(collection_id=collection_id, abs_item_id=body.abs_item_id))

    await db.refresh(coll, ["items"])
    return _to_detail(coll)


@router.delete("/collections/{collection_id}/items/{item_id}", status_code=204)
async def remove_item(
    collection_id: int,
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin():
        row = (
            await db.execute(
                select(CollectionItem).where(
                    CollectionItem.collection_id == collection_id,
                    CollectionItem.abs_item_id == item_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Item not in collection")
        await db.delete(row)
