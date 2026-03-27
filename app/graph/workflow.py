from typing import Any, List, TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from app.domain.services.intent_service import IntentService
from app.infrastructure.llm_client import llm_client


class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    message: str
    messages: List[Any]
    answer: str


def _intent_node(state: AgentState) -> AgentState:
    message = state.get("message", "")
    if not message:
        messages = state.get("messages") or []
        if messages and isinstance(messages[-1], HumanMessage):
            message = messages[-1].content or ""
    try:
        use_small_model = len(message) <= 120
        answer = llm_client.generate(message, use_small=use_small_model)
        if answer:
            return {"answer": answer}
    except Exception:
        # LLM 不可用时，回退到规则回复，保证服务可用性
        pass
    return {"answer": IntentService.build_answer(message)}


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("intent", _intent_node)
    graph.set_entry_point("intent")
    graph.add_edge("intent", END)
    return graph.compile()
