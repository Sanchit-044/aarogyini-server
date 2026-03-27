"""
Aarogyini Chatbot - Configuration
Environment-based settings management.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LLM Configuration
    OPENAI_API_KEY: str = "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"
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