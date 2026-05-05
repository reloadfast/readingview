from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.settings import SettingsPatch, SettingsRead

router = APIRouter()

_ENCRYPTED = {"abs_token", "llm_api_key", "apprise_url"}
# Map API field names to model column names for encrypted fields
_API_TO_COL = {"llm_api_key": "llm_api_key_enc"}


async def _get_or_create(db: AsyncSession) -> Settings:
    row = await db.get(Settings, 1)
    if row is None:
        row = Settings(id=1)
        db.add(row)
        await db.flush()
    return row


def _mask(row: Settings) -> SettingsRead:
    return SettingsRead(
        abs_url=row.abs_url,
        abs_token="" if row.abs_token else None,
        recommender_enabled=row.recommender_enabled,
        recommender_vector_backend=row.recommender_vector_backend,
        recommender_embed_model=row.recommender_embed_model,
        recommender_top_k=row.recommender_top_k,
        recommender_min_similarity=row.recommender_min_similarity,
        llm_type=row.llm_type,
        llm_endpoint=row.llm_endpoint,
        llm_model=row.llm_model,
        llm_api_key="" if row.llm_api_key_enc else None,
        notifications_enabled=row.notifications_enabled,
        apprise_url="" if row.apprise_url else None,
        notify_days_before=row.notify_days_before,
        notify_time=row.notify_time,
        timezone=row.timezone,
    )


@router.get("/settings", response_model=SettingsRead)
async def get_settings(db: AsyncSession = Depends(get_db)) -> SettingsRead:
    async with db.begin():
        row = await _get_or_create(db)
    return _mask(row)


@router.patch("/settings", response_model=SettingsRead)
async def patch_settings(
    patch: SettingsPatch,
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    updates = patch.model_dump(exclude_unset=True)

    async with db.begin():
        row = await _get_or_create(db)

        for api_field, value in updates.items():
            col = _API_TO_COL.get(api_field, api_field)
            if api_field in _ENCRYPTED and value is not None:
                value = encrypt(value)
            setattr(row, col, value)

    return _mask(row)
