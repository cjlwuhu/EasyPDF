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
