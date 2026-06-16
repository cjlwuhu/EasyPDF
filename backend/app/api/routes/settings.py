from fastapi import APIRouter

from app.schemas.settings import PublicSettings
from app.services.settings import public_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=PublicSettings)
def get_settings():
    return public_settings()
