from pydantic import BaseModel


class CollectionOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: str
    book_count: int

    class Config:
        from_attributes = True


class CollectionDetail(CollectionOut):
    item_ids: list[str]


class CreateCollectionRequest(BaseModel):
    name: str
    description: str | None = None


class PatchCollectionRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class AddItemRequest(BaseModel):
    abs_item_id: str
