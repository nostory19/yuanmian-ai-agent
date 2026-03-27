import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "yuanmian-ai-agent"
    host: str = "0.0.0.0"
    port: int = 8291
    debug: bool = True

    # OpenAI-compatible 主模型
    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com"
    openai_model_name: str = "deepseek-chat"
    openai_max_output_tokens: int = 800

    # OpenAI-compatible 小模型
    openai_small_api_key: str = ""
    openai_small_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    openai_small_model_name: str = "qwen-turbo"
    openai_small_max_output_tokens: int = 800


settings = Settings(
    app_name=os.getenv("APP_NAME", "yuanmian-ai-agent"),
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8291")),
    debug=os.getenv("DEBUG", "true").lower() == "true",
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
    openai_model_name=os.getenv("OPENAI_MODEL_NAME", "deepseek-chat"),
    openai_max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "800")),
    openai_small_api_key=os.getenv("OPENAI_SMALL_API_KEY", ""),
    openai_small_base_url=os.getenv("OPENAI_SMALL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    openai_small_model_name=os.getenv("OPENAI_SMALL_MODEL_NAME", "qwen-turbo"),
    openai_small_max_output_tokens=int(os.getenv("OPENAI_SMALL_MAX_OUTPUT_TOKENS", "800")),
)
