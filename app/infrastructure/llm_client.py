import json
from typing import AsyncIterator, Tuple
from urllib import error, request

import httpx
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
        system_prompt: str,
        message: str,
    ) -> str:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 未配置")
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
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

    def generate(
        self,
        message: str,
        use_small: bool = False,
        system_prompt: str = "你是一个有帮助的 AI 助手。",
    ) -> str:
        if use_small:
            return self._call_chat_api(
                api_key=settings.openai_small_api_key,
                base_url=settings.openai_small_base_url,
                model_name=settings.openai_small_model_name,
                max_output_tokens=settings.openai_small_max_output_tokens,
                system_prompt=system_prompt,
                message=message,
            )
        return self._call_chat_api(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=settings.openai_model_name,
            max_output_tokens=settings.openai_max_output_tokens,
            system_prompt=system_prompt,
            message=message,
        )

    def _stream_credentials(self, use_small: bool) -> Tuple[str, str, str, int]:
        if use_small:
            return (
                settings.openai_small_api_key,
                settings.openai_small_base_url,
                settings.openai_small_model_name,
                settings.openai_small_max_output_tokens,
            )
        return (
            settings.openai_api_key,
            settings.openai_base_url,
            settings.openai_model_name,
            settings.openai_max_output_tokens,
        )

    async def astream(
        self,
        message: str,
        use_small: bool = False,
        system_prompt: str = "你是一个有帮助的 AI 助手。",
    ) -> AsyncIterator[str]:
        api_key, base_url, model_name, max_tokens = self._stream_credentials(use_small)
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 未配置")
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": True,
        }
        timeout = httpx.Timeout(120.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    detail = (await e.response.aread()).decode("utf-8", errors="ignore")
                    raise RuntimeError(
                        f"LLM HTTPError {e.response.status_code}: {detail}"
                    ) from e
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith(":"):
                        continue
                    data = None
                    if line.startswith("data: "):
                        data = line[6:]
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                    if data is None:
                        continue
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if not content and isinstance(choices[0].get("message"), dict):
                        content = (choices[0]["message"] or {}).get("content") or ""
                    if content:
                        yield content


llm_client = LlmClient()
