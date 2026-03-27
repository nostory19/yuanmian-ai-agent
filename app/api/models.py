from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    user_id: str = Field(default="anonymous", description="用户 ID")
    message: str = Field(..., description="用户消息")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    source: str = "langgraph-agent"
