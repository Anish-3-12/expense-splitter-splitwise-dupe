from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class ReceiptItemSchema(BaseModel):
    description: str
    quantity: Decimal = Decimal("1.00")
    unit_price: Decimal
    line_total: Decimal
    confidence: Optional[Decimal] = Decimal("1.00")
    is_ambiguous: Optional[bool] = False
    ambiguity_reason: Optional[str] = None

class ReceiptExtractRequest(BaseModel):
    file_path: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    group_id: Optional[int] = None

class ReceiptExtractResponse(BaseModel):
    merchant: Optional[str] = "Unknown Merchant"
    receipt_date: Optional[str] = None
    currency: str = "USD"
    currency_symbol: str = "$"
    currency_evidence: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    discounts: Decimal = Decimal("0.00")
    other_charges: Decimal = Decimal("0.00")
    item_sum: Optional[Decimal] = None
    total: Decimal
    items: List[ReceiptItemSchema] = []
    warnings: List[str] = []
    validation_status: str = "RECONCILED"  # RECONCILED, DISCREPANCY_DETECTED, AMBIGUOUS_ITEMS
    discrepancy_amount: Decimal = Decimal("0.00")
    is_item_subtotal_reconciled: bool = False
    is_grand_total_reconciled: bool = False
    is_ambiguous: bool = False
    raw_ocr_text: Optional[str] = None
