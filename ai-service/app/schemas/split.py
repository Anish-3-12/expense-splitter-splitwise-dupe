from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal

class GroupMemberSchema(BaseModel):
    id: int
    name: str
    email: Optional[str] = ""

class ExpenseItemDraftSchema(BaseModel):
    id: Optional[str] = None
    description: str
    amount: Decimal

class ItemAllocationSchema(BaseModel):
    item_id: Optional[str] = None
    item_description: Optional[str] = None
    participant_ids: List[int]
    split_type: Optional[str] = "EQUAL" # EQUAL, PERCENT, CUSTOM

class ParticipantAllocationSchema(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    share_amount: Optional[Decimal] = None
    percent: Optional[Decimal] = None

class SplitInterpretRequest(BaseModel):
    instruction: str
    group_members: List[GroupMemberSchema]
    total_amount: Optional[Decimal] = None
    items: Optional[List[ExpenseItemDraftSchema]] = []
    payer_id: Optional[int] = None

class SplitInterpretResponse(BaseModel):
    original_instruction: str
    description: Optional[str] = None
    total_amount: Optional[Decimal] = None
    payer_id: Optional[int] = None
    split_type: Optional[str] = "EQUAL"
    allocations: List[ItemAllocationSchema] = []
    participant_allocations: List[ParticipantAllocationSchema] = []
    unresolved_references: List[str] = []
    clarification_required: bool = False
    clarification_question: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 1.0
