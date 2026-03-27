"""
Aarogyini Chatbot - Configuration
Environment-based settings management.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"           # "openai" | "ollama"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_HOST: str = None

    # App Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    SECRET_KEY: str = "your-secret-key-change-in-production"
    DEBUG: bool = True

    # Safety
    MAX_CONVERSATION_TURNS: int = 20
    MAX_TOKENS: int = 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()