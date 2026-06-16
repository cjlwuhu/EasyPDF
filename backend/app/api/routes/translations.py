from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.session import SessionLocal
from app.schemas.translations import StartDocumentTranslationResponse, TranslateParagraphRequest, TranslateParagraphResponse
from app.services.translations import create_document_translation_job, run_document_translation, translate_paragraph

router = APIRouter(prefix="/translations", tags=["translations"])


@router.post("/paragraph", response_model=TranslateParagraphResponse)
async def post_translate_paragraph(payload: TranslateParagraphRequest, db: Session = Depends(get_db)):
    try:
        paragraph = await translate_paragraph(db, payload.paragraph_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TranslateParagraphResponse(
        paragraph_id=paragraph.id,
        translated_text=paragraph.translated_text,
        status=paragraph.status.value,
    )


async def run_job_in_new_session(job_id: int) -> None:
    db = SessionLocal()
    try:
        await run_document_translation(db, job_id)
    finally:
        db.close()


@router.post("/documents/{document_id}/start", response_model=StartDocumentTranslationResponse)
def start_document_translation(document_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = create_document_translation_job(db, document_id)
    background_tasks.add_task(run_job_in_new_session, job.id)
    return StartDocumentTranslationResponse(job_id=job.id, status=job.status, total_count=job.total_count)
