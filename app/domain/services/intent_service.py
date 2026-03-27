class IntentService:
    @staticmethod
    def build_answer(message: str) -> str:
        if "旅游" in message or "面试" in message:
            return f"我理解你的目标，下面给你结构化建议：\n{message}"
        return f"这是一个通用问题，我给你简要建议：\n{message}"
