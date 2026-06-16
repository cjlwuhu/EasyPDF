from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GlossaryTerm


def create_term(
    db: Session,
    source_term: str,
    target_term: str,
    note: str = "",
    keep_english: bool = False,
) -> GlossaryTerm:
    term = GlossaryTerm(
        source_term=source_term.strip(),
        target_term=target_term.strip(),
        note=note.strip(),
        keep_english=keep_english,
        enabled=True,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def list_terms(db: Session) -> list[GlossaryTerm]:
    return list(db.scalars(select(GlossaryTerm).order_by(GlossaryTerm.source_term)))


def list_enabled_terms(db: Session) -> list[GlossaryTerm]:
    statement = select(GlossaryTerm).where(GlossaryTerm.enabled.is_(True)).order_by(GlossaryTerm.source_term)
    return list(db.scalars(statement))
