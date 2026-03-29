import asyncio
from typing import AsyncIterator

from app.infrastructure.llm_client import llm_client

FLOAT_SYSTEM_PROMPT = (
    "你是「远面」平台的悬浮助手，用简洁、友好的中文回答用户关于产品使用、通用技术等问题。"
    "不要编造系统不存在的功能；不确定时请直说不确定。"
)


class SimpleAssistantService:
    """单轮直连 LLM，不经 LangGraph / 面试多 Agent。"""

    async def chat(self, session_id: str, user_id: str, message: str) -> dict:
        answer = await asyncio.to_thread(
            llm_client.generate,
            message,
            False,
            FLOAT_SYSTEM_PROMPT,
        )
        return {
            "session_id": session_id,
            "answer": answer or "",
            "source": "simple-llm",
        }

    async def chat_stream(
        self, session_id: str, user_id: str, message: str
    ) -> AsyncIterator[str]:
        async for chunk in llm_client.astream(
            message, use_small=False, system_prompt=FLOAT_SYSTEM_PROMPT
        ):
            if chunk:
                yield chunk

