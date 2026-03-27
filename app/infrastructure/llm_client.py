class LlmClient:
    """
    预留 LLM 客户端封装。
    后续可在这里接 OpenAI、DeepSeek 等模型。
    """

    def generate(self, prompt: str) -> str:
        return prompt
