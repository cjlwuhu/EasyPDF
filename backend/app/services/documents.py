from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import BACKEND_DIR, settings
from app.db.models import Block, BlockType, Document, Page, Paragraph
from app.services.pdf_parser import ParsedBlock, order_text_blocks, parse_pdf


def storage_root() -> Path:
    root = Path(settings.storage_dir)
    if not root.is_absolute():
        root = BACKEND_DIR / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_upload(file: UploadFile) -> Path:
    uploads_dir = storage_root() / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "upload.pdf").name
    suffix = Path(original_name).suffix.lower() or ".pdf"
    saved_path = uploads_dir / f"{uuid4().hex}{suffix}"

    with saved_path.open("wb") as destination:
        shutil.copyfileobj(file.file, destination)

    return saved_path


def create_document_from_pdf(db: Session, file: UploadFile) -> Document:
    saved_path = save_upload(file)
    original_filename = Path(file.filename or "upload.pdf").name
    parsed_pdf = parse_pdf(saved_path)

    document = Document(
        title=Path(original_filename).stem or original_filename,
        original_filename=original_filename,
        file_path=str(saved_path),
        status="parsed",
    )
    db.add(document)
    db.flush()

    pages_by_number: dict[int, Page] = {}
    for parsed_page in parsed_pdf.pages:
        page = Page(
            document_id=document.id,
            page_number=parsed_page.page_number,
            width=parsed_page.width,
            height=parsed_page.height,
        )
        db.add(page)
        db.flush()
        pages_by_number[parsed_page.page_number] = page

    for parsed_block in parsed_pdf.blocks:
        page = pages_by_number[parsed_block.page_number]
        db.add(
            Block(
                document_id=document.id,
                page_id=page.id,
                block_type=BlockType.text,
                order_index=parsed_block.order_index,
                x0=parsed_block.x0,
                y0=parsed_block.y0,
                x1=parsed_block.x1,
                y1=parsed_block.y1,
                content=parsed_block.text,
            )
        )

    for parsed_paragraph in parsed_pdf.paragraphs:
        db.add(
            Paragraph(
                document_id=document.id,
                page_number=parsed_paragraph.page_number,
                order_index=parsed_paragraph.order_index,
                source_text=parsed_paragraph.source_text,
                x0=parsed_paragraph.x0,
                y0=parsed_paragraph.y0,
                x1=parsed_paragraph.x1,
                y1=parsed_paragraph.y1,
            )
        )

    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
    return list(db.scalars(statement))


def get_document(db: Session, document_id: int) -> Document | None:
    statement = (
        select(Document)
        .options(selectinload(Document.pages), selectinload(Document.paragraphs))
        .where(Document.id == document_id)
    )
    return db.scalar(statement)


def order_document_paragraphs(document: Document) -> list[Paragraph]:
    widths = {page.page_number: page.width for page in document.pages}
    ordered: list[Paragraph] = []

    for page_number in sorted({paragraph.page_number for paragraph in document.paragraphs}):
        page_paragraphs = sorted(
            (paragraph for paragraph in document.paragraphs if paragraph.page_number == page_number),
            key=lambda item: item.order_index,
        )
        blocks = [
            ParsedBlock(
                page_number=page_number,
                order_index=paragraph.order_index,
                x0=paragraph.x0,
                y0=paragraph.y0,
                x1=paragraph.x1,
                y1=paragraph.y1,
                text=str(index),
            )
            for index, paragraph in enumerate(page_paragraphs)
        ]
        page_width = widths.get(page_number, max((paragraph.x1 for paragraph in page_paragraphs), default=0))
        ordered.extend(page_paragraphs[int(block.text)] for block in order_text_blocks(blocks, page_width))

    return ordered
