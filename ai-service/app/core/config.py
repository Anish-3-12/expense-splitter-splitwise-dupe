import os
from typing import Optional

class Settings:
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    AI_SERVICE_PORT: int = int(os.getenv("AI_SERVICE_PORT", "8000"))
    INTERNAL_API_SECRET: str = os.getenv("INTERNAL_API_SECRET", "splitwise-ai-internal-secret-2026")
    INFERENCE_TIMEOUT: int = int(os.getenv("INFERENCE_TIMEOUT", "90"))
    MAX_IMAGE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

settings = Settings()
