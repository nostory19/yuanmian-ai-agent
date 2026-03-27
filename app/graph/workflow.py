from typing import TypedDict

from langgraph.graph import END, StateGraph
from app.domain.services.intent_service import IntentService


class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    message: str
    answer: str


def _intent_node(state: AgentState) -> AgentState:
    message = state.get("message", "")
    return {"answer": IntentService.build_answer(message)}


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("intent", _intent_node)
    graph.set_entry_point("intent")
    graph.add_edge("intent", END)
    return graph.compile()
