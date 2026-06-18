from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models import ParagraphStatus


class ParagraphRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_number: int
    order_index: int
    source_text: str
    translated_text: str
    status: ParagraphStatus
    x0: float
    y0: float
    x1: float
    y1: float
    reading_order: int = 0


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_filename: str
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentRead):
    paragraphs: list[ParagraphRead]
