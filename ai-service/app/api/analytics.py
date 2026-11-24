from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_internal_secret
from app.schemas.analytics import AnomalyDetectRequest, AnomalyDetectResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/internal/v1/analytics", tags=["analytics"])

@router.post("/detect-anomalies", response_model=AnomalyDetectResponse, dependencies=[Depends(verify_internal_secret)])
async def detect_anomalies(request: AnomalyDetectRequest):
    try:
        return analytics_service.detect_anomalies(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
