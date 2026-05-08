from pydantic import BaseModel


class NoteOut(BaseModel):
    body: str | None

    model_config = {"from_attributes": True}


class NotePut(BaseModel):
    body: str
