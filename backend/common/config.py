
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    AGENT_URL: Optional[str] = None
    CHROMA_SERVER_IP: str = "localhost"
    CHROMA_SERVER_PORT: int = 8001

    class Config:
        env_file = ".env"

settings = Settings()

