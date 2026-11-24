from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class CategorizeRequest(BaseModel):
    merchant: Optional[str] = None
    note: Optional[str] = None
    amount: Optional[Decimal] = None

class CategorizeResponse(BaseModel):
    category: str
    confidence: float
    method: str # "RULE", "KEYWORD", "LLM", "DEFAULT"
