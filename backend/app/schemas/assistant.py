from pydantic import BaseModel


class AskAssistantRequest(BaseModel):
    question: str
    selected_text: str
    source_text: str = ""


class AskAssistantResponse(BaseModel):
    answer: str
