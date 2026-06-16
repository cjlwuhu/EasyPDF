from pydantic import BaseModel


class ReplaceTranslationRequest(BaseModel):
    paragraph_id: int
    new_text: str


class ReplaceTranslationResponse(BaseModel):
    paragraph_id: int
    translated_text: str
    status: str
