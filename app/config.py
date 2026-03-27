from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "yuanmian-ai-agent"
    host: str = "0.0.0.0"
    port: int = 8291
    debug: bool = True


settings = Settings()
