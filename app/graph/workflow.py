import json
from typing import Any, Dict, List, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from app.domain.services.intent_service import IntentService
from app.infrastructure.llm_client import llm_client


class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    message: str
    messages: List[Any]
    question: str
    score: int
    weakness: str
    follow_up_question: str
    report: str
    next_action: str
    agent_trace: List[str]
    answer: str


def _extract_message(state: AgentState) -> str:
    message = state.get("message", "")
    if not message:
        messages = state.get("messages") or []
        if messages and isinstance(messages[-1], HumanMessage):
            message = messages[-1].content or ""
    return message


def _safe_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except Exception:
        return {}


def _interviewer_node(state: AgentState) -> AgentState:
    message = _extract_message(state)
    prompt = (
        "你是 Interviewer Agent（技术面试官）。"
        "基于候选人刚才的输入，给出下一道技术面试题。"
        "要求：问题清晰、可继续追问、不要输出解析。"
    )
    try:
        question = llm_client.generate(message, use_small=True, system_prompt=prompt)
        if not question:
            question = f"请你围绕“{message}”讲一下核心思路，并分析复杂度。"
    except Exception:
        question = f"请你围绕“{message}”讲一下核心思路，并分析复杂度。"
    trace = list(state.get("agent_trace") or [])
    trace.append("interviewer")
    return {"question": question, "agent_trace": trace}


def _evaluator_node(state: AgentState) -> AgentState:
    message = _extract_message(state)
    question = state.get("question", "")
    prompt = (
        "你是 Evaluator Agent（评估官）。"
        "请严格输出 JSON："
        '{"score":0-100整数,"weakness":"一句话短板","next_action":"follow_up 或 report"}。'
        "评分低于70时 next_action 必须是 follow_up。"
    )
    user_input = f"面试题：{question}\n候选人回答：{message}"
    score = 75
    weakness = "复杂度分析仍可加强"
    next_action: Literal["follow_up", "report"] = "report"
    try:
        # 按照面试题和用户回答，评估官给出评估结果
        resp = llm_client.generate(user_input, use_small=False, system_prompt=prompt)
        data = _safe_json(resp)
        parsed_score = int(data.get("score", score))
        score = max(0, min(100, parsed_score))
        weakness = str(data.get("weakness", weakness))
        next_action = "follow_up" if score < 70 else "report"
    except Exception:
        if len(message) < 40:
            score = 62
            weakness = "回答较短，细节不足"
            next_action = "follow_up"
    trace = list(state.get("agent_trace") or [])
    trace.append("evaluator")
    return {
        "score": score,
        "weakness": weakness,
        "next_action": next_action,
        "agent_trace": trace,
    }


def _follow_up_node(state: AgentState) -> AgentState:
    message = _extract_message(state)
    weakness = state.get("weakness", "细节不够")
    prompt = (
        "你是 Follow-up Agent（追问专家）。"
        "请基于候选人短板，输出一个更深入的追问问题。"
    )
    user_input = f"候选人回答：{message}\n短板：{weakness}"
    try:
        follow_up_q = llm_client.generate(user_input, use_small=True, system_prompt=prompt)
        if not follow_up_q:
            follow_up_q = f"你提到的方案在高并发下如何优化？请重点补充：{weakness}"
    except Exception:
        follow_up_q = f"你提到的方案在高并发下如何优化？请重点补充：{weakness}"
    answer = f"追问（Follow-up Agent）：{follow_up_q}"
    trace = list(state.get("agent_trace") or [])
    trace.append("follow_up")
    return {"follow_up_question": follow_up_q, "answer": answer, "agent_trace": trace}


def _report_node(state: AgentState) -> AgentState:
    score = int(state.get("score", 75))
    weakness = state.get("weakness", "复杂度分析可加强")
    message = _extract_message(state)
    prompt = (
        "你是 Report Agent（总结官）。"
        "输出一段简洁面试报告，包含：得分、优点、短板、下一步建议。"
    )
    user_input = f"得分：{score}\n短板：{weakness}\n候选人回答：{message}"
    try:
        report = llm_client.generate(user_input, use_small=False, system_prompt=prompt)
        if not report:
            raise RuntimeError("empty report")
    except Exception:
        report = f"得分：{score}\n优点：思路基本完整\n短板：{weakness}\n建议：补齐复杂度与边界分析。"
    trace = list(state.get("agent_trace") or [])
    trace.append("report")
    return {"report": report, "answer": report, "agent_trace": trace}


def _route_next(state: AgentState) -> str:
    return "follow_up" if state.get("next_action") == "follow_up" else "report"


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("interviewer", _interviewer_node)
    graph.add_node("evaluator", _evaluator_node)
    graph.add_node("follow_up", _follow_up_node)
    graph.add_node("report_agent", _report_node)
    graph.set_entry_point("interviewer")
    graph.add_edge("interviewer", "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        _route_next,
        {"follow_up": "follow_up", "report": "report_agent"},
    )
    graph.add_edge("follow_up", END)
    graph.add_edge("report_agent", END)
    return graph.compile()

