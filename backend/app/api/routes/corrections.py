from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.corrections import ReplaceTranslationRequest, ReplaceTranslationResponse
from app.services.corrections import replace_translation

router = APIRouter(prefix="/corrections", tags=["corrections"])


@router.post("/replace", response_model=ReplaceTranslationResponse)
def post_replace_translation(payload: ReplaceTranslationRequest, db: Session = Depends(get_db)):
    try:
        paragraph = replace_translation(db, payload.paragraph_id, payload.new_text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplaceTranslationResponse(
        paragraph_id=paragraph.id,
        translated_text=paragraph.translated_text,
        status=paragraph.status.value,
    )
