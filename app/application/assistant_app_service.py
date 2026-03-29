import json
from typing import Any, AsyncIterator, Dict

from langchain_core.messages import HumanMessage
from loguru import logger

from app.graph.workflow import build_workflow

META_PREFIX = "__AGENT_META__"

_META_KEYS = (
    "answer",
    "next_action",
    "score",
    "question",
    "weakness",
    "follow_up_question",
    "report",
    "agent_trace",
)


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
        merged: Dict[str, Any] = {}
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
                        for key in _META_KEYS:
                            if key in output:
                                merged[key] = output[key]
                        answer = output.get("answer")
                        if isinstance(answer, str):
                            fallback_answer = answer

            if not emitted and fallback_answer:
                # 按小块输出，避免前端每个字符单独成行（仍是一次性生成后的分块）
                step = 24
                for i in range(0, len(fallback_answer), step):
                    yield fallback_answer[i : i + step]

            # 流式结束后附带结构化字段，供网关/前端更新状态（单行 JSON）
            meta: Dict[str, Any] = {"_meta": True, "session_id": session_id}
            for key in _META_KEYS:
                if key in merged:
                    meta[key] = merged[key]
            yield META_PREFIX + json.dumps(meta, ensure_ascii=False)
        except Exception as e:
            logger.exception("assistant stream error: {}", e)
            yield "\n错误: 服务暂时不可用，请稍后重试"

    async def chat(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
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
            return {
                "session_id": session_id,
                "answer": answer if isinstance(answer, str) and answer else "未生成回答",
                "source": "langgraph-multi-agent",
                "next_action": result.get("next_action", "report"),
                "score": result.get("score"),
                "question": result.get("question"),
                "weakness": result.get("weakness"),
                "follow_up_question": result.get("follow_up_question"),
                "report": result.get("report"),
                "agent_trace": result.get("agent_trace") or [],
            }
        except Exception as e:
            logger.exception("assistant chat error: {}", e)
            return {
                "session_id": session_id,
                "answer": "服务暂时不可用，请稍后重试",
                "source": "langgraph-multi-agent",
                "next_action": "report",
                "agent_trace": [],
            }
