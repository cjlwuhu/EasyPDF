from fastapi import APIRouter

from app.schemas.assistant import AskAssistantRequest, AskAssistantResponse
from app.services.ai_client import AIClient

router = APIRouter(prefix="/assistant", tags=["assistant"])


def build_assistant_prompt(payload: AskAssistantRequest) -> str:
    return (
        "You are an assistant helping a user understand and revise translated PDF text.\n\n"
        f"Question:\n{payload.question}\n\n"
        f"Selected translation text:\n{payload.selected_text}\n\n"
        f"Source text:\n{payload.source_text}"
    )


@router.post("/ask", response_model=AskAssistantResponse)
async def ask_assistant(payload: AskAssistantRequest):
    answer = await AIClient().complete(build_assistant_prompt(payload))
    return AskAssistantResponse(answer=answer)
