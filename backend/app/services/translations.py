from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Paragraph, ParagraphStatus, TranslationJob
from app.services.ai_client import AIClient
from app.services.glossary import list_enabled_terms
from app.services.prompts import GlossaryPromptTerm, build_translation_prompt


def glossary_for_prompt(db: Session) -> list[GlossaryPromptTerm]:
    return [
        GlossaryPromptTerm(
            source_term=term.source_term,
            target_term=term.target_term,
            keep_english=term.keep_english,
        )
        for term in list_enabled_terms(db)
    ]


async def translate_paragraph(db: Session, paragraph_id: int, ai_client: AIClient | None = None) -> Paragraph:
    paragraph = db.get(Paragraph, paragraph_id)
    if paragraph is None:
        raise ValueError("Paragraph not found")

    paragraph.status = ParagraphStatus.translating
    db.commit()
    db.refresh(paragraph)

    client = ai_client or AIClient()
    prompt = build_translation_prompt(
        source_text=paragraph.source_text,
        context_before="",
        context_after="",
        glossary=glossary_for_prompt(db),
    )

    try:
        paragraph.translated_text = await client.complete(prompt)
        paragraph.status = ParagraphStatus.translated
    except Exception:
        paragraph.status = ParagraphStatus.failed
        db.commit()
        raise

    db.commit()
    db.refresh(paragraph)
    return paragraph


def create_document_translation_job(db: Session, document_id: int) -> TranslationJob:
    paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == document_id)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )
    job = TranslationJob(document_id=document_id, status="queued", total_count=len(paragraphs))
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


async def run_document_translation(db: Session, job_id: int, initial_pages: int = 3) -> TranslationJob:
    job = db.get(TranslationJob, job_id)
    if job is None:
        raise ValueError("Translation job not found")

    job.status = "running"
    db.commit()

    priority_paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == job.document_id)
            .where(Paragraph.page_number <= initial_pages)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )
    remaining_paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == job.document_id)
            .where(Paragraph.page_number > initial_pages)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )

    for paragraph in [*priority_paragraphs, *remaining_paragraphs]:
        try:
            await translate_paragraph(db, paragraph.id)
            job.completed_count += 1
        except Exception:
            job.failed_count += 1
        db.commit()

    job.status = "completed" if job.failed_count == 0 else "completed_with_errors"
    db.commit()
    db.refresh(job)
    return job
