from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.documents import DocumentDetail, DocumentRead, ParagraphRead
from app.services.docx_export import build_translation_docx, safe_docx_filename
from app.services.documents import create_document_from_pdf, get_document, list_documents, order_document_paragraphs

router = APIRouter(prefix="/documents", tags=["documents"])


def _is_pdf(file: UploadFile) -> bool:
    filename = file.filename or ""
    return file.content_type == "application/pdf" or filename.lower().endswith(".pdf")


@router.get("", response_model=list[DocumentRead])
def get_documents(db: Session = Depends(get_db)):
    return list_documents(db)


@router.post("", response_model=DocumentRead)
def post_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not _is_pdf(file):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    return create_document_from_pdf(db, file)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    detail = DocumentDetail.model_validate(document)
    paragraphs = [
        ParagraphRead.model_validate(paragraph).model_copy(update={"reading_order": index})
        for index, paragraph in enumerate(order_document_paragraphs(document))
    ]
    return detail.model_copy(update={"paragraphs": paragraphs})


@router.get("/{document_id}/file")
def get_document_file(document_id: int, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(document.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=document.original_filename,
    )


@router.get("/{document_id}/translation.docx")
def get_translation_docx(document_id: int, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    translations = [
        paragraph.translated_text.strip()
        for paragraph in order_document_paragraphs(document)
        if paragraph.translated_text.strip()
    ]
    if not translations:
        raise HTTPException(status_code=409, detail="Document has no translated paragraphs")

    filename = safe_docx_filename(document.title)
    fallback_filename = filename if filename.isascii() else "translation.docx"
    payload = build_translation_docx(document.title, translations)
    return StreamingResponse(
        BytesIO(payload),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{fallback_filename}"; filename*=UTF-8\'\'{quote(filename)}'
            )
        },
    )
