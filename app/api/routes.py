from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.models import ChatRequest, ChatResponse
from app.application.assistant_app_service import AssistantAppService

router = APIRouter(prefix="/agent", tags=["agent"])
assistant_service = AssistantAppService()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = assistant_service.chat(request.session_id, request.user_id, request.message)
    return ChatResponse(session_id=request.session_id, answer=answer)


@router.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    answer = assistant_service.chat(request.session_id, request.user_id, request.message)

    async def event_generator():
        for line in answer.split("\n"):
            yield f"data: {line}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
