from typing import Any, AsyncIterator, Dict

from langchain_core.messages import HumanMessage
from loguru import logger

from app.graph.workflow import build_workflow


class AssistantAppService:
    def __init__(self):
        self.graph = build_workflow()

    async def chat_stream(
        self,
        session_id: str,
        user_id: str,
        message: str,
    ) -> AsyncIterator[str]:
        """
        流式对话：
        - 优先透传 graph 的 on_chat_model_stream token
        - 若没有 token 事件，回退为最终 answer 的字符流
        """
        config = {"configurable": {"thread_id": session_id}}
        initial_state: Dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "message": message,
            "messages": [HumanMessage(content=message)],
        }
        emitted = False
        fallback_answer = ""
        logger.info("assistant stream start, thread_id={}", session_id)
        try:
            async for event in self.graph.astream_events(initial_state, config=config, version="v2"):
                event_type = event.get("event")
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    content = getattr(chunk, "content", "") if chunk else ""
                    if isinstance(content, str) and content:
                        emitted = True
                        yield content
                elif event_type == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        answer = output.get("answer")
                        if isinstance(answer, str):
                            fallback_answer = answer

            if not emitted and fallback_answer:
                for ch in fallback_answer:
                    yield ch
        except Exception as e:
            logger.exception("assistant stream error: {}", e)
            yield "\n错误: 服务暂时不可用，请稍后重试"

    async def chat(self, session_id: str, user_id: str, message: str) -> str:
        config = {"configurable": {"thread_id": session_id}}
        initial_state: Dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "message": message,
            "messages": [HumanMessage(content=message)],
        }
        try:
            result = await self.graph.ainvoke(initial_state, config=config)
            answer = result.get("answer", "")
            return answer if isinstance(answer, str) and answer else "未生成回答"
        except Exception as e:
            logger.exception("assistant chat error: {}", e)
            return "服务暂时不可用，请稍后重试"
