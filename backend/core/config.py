
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    AGENT_URL: Optional[str] = None
    CHROMA_PERSIST_DIR: Optional[str] = None
    # add other settings as needed

    class Config:
        env_file = ".env"

settings = Settings()

