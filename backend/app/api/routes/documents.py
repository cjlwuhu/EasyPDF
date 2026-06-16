from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.documents import DocumentDetail, DocumentRead
from app.services.documents import create_document_from_pdf, get_document, list_documents

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
    return document


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
