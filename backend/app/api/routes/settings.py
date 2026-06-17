from fastapi import APIRouter, HTTPException

from app.schemas.settings import PublicSettings, UpdateAISettingsRequest
from app.services.settings import public_settings, update_ai_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=PublicSettings)
def get_settings():
    return public_settings()


@router.post("", response_model=PublicSettings)
def update_settings(payload: UpdateAISettingsRequest):
    try:
        return update_ai_settings(
            api_key=payload.api_key,
            base_url=payload.base_url,
            model_name=payload.model_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
