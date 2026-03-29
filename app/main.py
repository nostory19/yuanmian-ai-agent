from fastapi import FastAPI
from app.api.assistant_chat_routes import router as assistant_router
from app.api.routes import router as agent_router
from app.config import settings

# 初始化 FastAPI 应用
app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(agent_router)
app.include_router(assistant_router)
