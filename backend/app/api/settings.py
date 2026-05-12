from fastapi import APIRouter, Depends
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import encrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.settings import SettingsPatch, SettingsRead
from ..services import scheduler as scheduler_svc

router = APIRouter()

_ENCRYPTED = {"abs_token", "llm_api_key", "apprise_url"}


async def _get_or_create(db: AsyncSession) -> Settings:
    await db.execute(
        sqlite_insert(Settings).values(id=1).on_conflict_do_nothing(index_elements=["id"])
    )
    row = await db.get(Settings, 1)
    if row is None:
        raise RuntimeError("Settings row missing after INSERT OR IGNORE")
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
        recommender_explanations_enabled=row.recommender_explanations_enabled,
        llm_type=row.llm_type,
        llm_endpoint=row.llm_endpoint,
        llm_model=row.llm_model,
        llm_api_key="" if row.llm_api_key else None,
        notifications_enabled=row.notifications_enabled,
        apprise_url="" if row.apprise_url else None,
        notify_days_before=row.notify_days_before,
        notify_time=row.notify_time,
        timezone=row.timezone,
        releases_refresh_cron=row.releases_refresh_cron,
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
            if api_field in _ENCRYPTED and value is not None:
                value = encrypt(value)
            setattr(row, api_field, value)

    if "releases_refresh_cron" in updates and updates["releases_refresh_cron"]:
        scheduler_svc.reschedule_refresh(updates["releases_refresh_cron"])

    if any(k in updates for k in ("notify_time", "timezone")):
        scheduler_svc.reschedule_digest(row.notify_time, row.timezone)

    return _mask(row)
