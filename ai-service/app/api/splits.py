from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_internal_secret
from app.schemas.split import SplitInterpretRequest, SplitInterpretResponse
from app.services.split_service import split_service

router = APIRouter(prefix="/internal/v1/expenses", tags=["splits"])

@router.post("/interpret-split", response_model=SplitInterpretResponse, dependencies=[Depends(verify_internal_secret)])
async def interpret_split(request: SplitInterpretRequest):
    try:
        return await split_service.interpret_split(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
