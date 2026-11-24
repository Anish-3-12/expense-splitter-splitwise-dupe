from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_internal_secret
from app.schemas.receipt import ReceiptExtractRequest, ReceiptExtractResponse
from app.services.receipt_service import receipt_service

router = APIRouter(prefix="/internal/v1/receipts", tags=["receipts"])

@router.post("/extract", response_model=ReceiptExtractResponse, dependencies=[Depends(verify_internal_secret)])
async def extract_receipt(request: ReceiptExtractRequest):
    try:
        return await receipt_service.process_receipt(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
