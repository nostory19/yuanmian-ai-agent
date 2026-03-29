from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.models import ChatRequest, ChatResponse
from app.application.simple_assistant_service import SimpleAssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])
simple_service = SimpleAssistantService()


@router.get("/health")
async def health():
    return {"status": "ok", "mode": "simple-llm"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    resp = await simple_service.chat(
        request.session_id, request.user_id, request.message
    )
    return ChatResponse(
        session_id=resp["session_id"],
        answer=resp["answer"],
        source=resp.get("source", "simple-llm"),
    )


@router.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in simple_service.chat_stream(
            request.session_id, request.user_id, request.message
        ):
            yield f"data: {chunk}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
