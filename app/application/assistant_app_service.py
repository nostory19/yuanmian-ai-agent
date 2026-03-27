from app.graph.workflow import build_workflow


class AssistantAppService:
    def __init__(self):
        self.graph = build_workflow()

    def chat(self, session_id: str, user_id: str, message: str) -> str:
        result = self.graph.invoke(
            {"session_id": session_id, "user_id": user_id, "message": message}
        )
        return result.get("answer", "未生成回答")
