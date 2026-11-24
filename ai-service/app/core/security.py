from fastapi import Header, HTTPException, status
from app.core.config import settings

async def verify_internal_secret(x_internal_secret: str = Header(None)):
    """
    Validates that the incoming request has the correct internal service secret.
    If the caller is Spring Boot or internal test, the header must match settings.INTERNAL_API_SECRET.
    Health checks bypass this check.
    """
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized internal service request"
        )
    return True
