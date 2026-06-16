from sqlalchemy.orm import Session

from app.db.models import Correction, Paragraph, ParagraphStatus


def replace_translation(db: Session, paragraph_id: int, new_text: str) -> Paragraph:
    paragraph = db.get(Paragraph, paragraph_id)
    if paragraph is None:
        raise ValueError("Paragraph not found")

    correction = Correction(
        paragraph_id=paragraph.id,
        old_text=paragraph.translated_text,
        new_text=new_text,
    )
    paragraph.translated_text = new_text
    paragraph.status = ParagraphStatus.corrected
    db.add(correction)
    db.commit()
    db.refresh(paragraph)
    return paragraph
