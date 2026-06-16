from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.glossary import GlossaryTermCreate, GlossaryTermRead
from app.services.glossary import create_term, list_terms

router = APIRouter(prefix="/glossary", tags=["glossary"])


@router.get("", response_model=list[GlossaryTermRead])
def get_glossary(db: Session = Depends(get_db)):
    return list_terms(db)


@router.post("", response_model=GlossaryTermRead)
def post_glossary(payload: GlossaryTermCreate, db: Session = Depends(get_db)):
    return create_term(
        db,
        source_term=payload.source_term,
        target_term=payload.target_term,
        note=payload.note,
        keep_english=payload.keep_english,
    )
