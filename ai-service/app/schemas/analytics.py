from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal

class ExpenseDataPoint(BaseModel):
    expense_id: int
    amount: Decimal
    payer_id: int
    category: Optional[str] = "Other"
    created_at: Optional[str] = None
    note: Optional[str] = None

class AnomalyDetectRequest(BaseModel):
    group_id: int
    historical_expenses: List[ExpenseDataPoint]
    target_expense_id: Optional[int] = None

class AnomalyResultItem(BaseModel):
    expense_id: int
    amount: Decimal
    status: str # "NORMAL", "UNUSUAL", "REQUIRES_REVIEW", "INSUFFICIENT_DATA"
    anomaly_score: float
    reason: str

class AnomalyDetectResponse(BaseModel):
    results: List[AnomalyResultItem]
    method_used: str # "ISOLATION_FOREST", "STATISTICAL_IQR", "INSUFFICIENT_DATA"
    historical_count: int
    mean_amount: Optional[float] = None
    std_amount: Optional[float] = None
