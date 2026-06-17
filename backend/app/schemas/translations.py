from pydantic import BaseModel


class TranslateParagraphRequest(BaseModel):
    paragraph_id: int


class TranslateParagraphResponse(BaseModel):
    paragraph_id: int
    translated_text: str
    status: str


class StartDocumentTranslationResponse(BaseModel):
    job_id: int
    status: str
    total_count: int


class TranslationJobResponse(BaseModel):
    job_id: int
    document_id: int
    status: str
    total_count: int
    completed_count: int
    failed_count: int
