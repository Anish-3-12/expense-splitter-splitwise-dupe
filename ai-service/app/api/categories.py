from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_internal_secret
from app.schemas.category import CategorizeRequest, CategorizeResponse
from app.services.category_service import category_service

router = APIRouter(prefix="/internal/v1/expenses", tags=["categories"])

@router.post("/categorize", response_model=CategorizeResponse, dependencies=[Depends(verify_internal_secret)])
async def categorize_expense(request: CategorizeRequest):
    try:
        return await category_service.categorize(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
