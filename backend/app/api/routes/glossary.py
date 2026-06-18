from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.glossary import GlossaryTermCreate, GlossaryTermRead
from app.services.glossary import create_term, delete_term, list_terms

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


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)):
    if not delete_term(db, term_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Glossary term not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
