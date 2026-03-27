import json
from urllib import request, error

from loguru import logger

from app.config import settings


class LlmClient:
    """
    OpenAI 兼容协议客户端（支持 DeepSeek / DashScope 兼容接口）。
    """

    @staticmethod
    def _call_chat_api(
        *,
        api_key: str,
        base_url: str,
        model_name: str,
        max_output_tokens: int,
        message: str,
    ) -> str:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 未配置")
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_output_tokens,
            "temperature": 0.7,
            "stream": False,
        }
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                return (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
        except error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM HTTPError {e.code}: {detail}") from e
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}") from e

    def generate(self, message: str, use_small: bool = False) -> str:
        if use_small:
            return self._call_chat_api(
                api_key=settings.openai_small_api_key,
                base_url=settings.openai_small_base_url,
                model_name=settings.openai_small_model_name,
                max_output_tokens=settings.openai_small_max_output_tokens,
                message=message,
            )
        return self._call_chat_api(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=settings.openai_model_name,
            max_output_tokens=settings.openai_max_output_tokens,
            message=message,
        )


llm_client = LlmClient()
