from fastapi import APIRouter
from app.providers.ollama_provider import ollama_provider

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"status": "ok", "service": "splitwise-ai-microservice"}

@router.get("/ready")
async def readiness():
    ollama_status = await ollama_provider.health_check()
    return {
        "status": "ready" if ollama_status.get("status") == "healthy" else "degraded",
        "ollama": ollama_status
    }
