from fastapi import APIRouter, HTTPException

from app.schemas.settings import PublicSettings, TestAISettingsResponse, UpdateAISettingsRequest
from app.services.settings import check_ai_connection, public_settings, update_ai_settings

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


@router.post("/test-ai", response_model=TestAISettingsResponse)
async def test_settings_ai(payload: UpdateAISettingsRequest):
    try:
        return await check_ai_connection(
            api_key=payload.api_key,
            base_url=payload.base_url,
            model_name=payload.model_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        return TestAISettingsResponse(ok=False, message=str(exc))
