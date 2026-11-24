import re
from decimal import Decimal
from typing import Dict, Any, List, Set, Optional
from app.core.logging import logger
from app.providers.ollama_provider import ollama_provider
from app.schemas.split import (
    SplitInterpretRequest,
    SplitInterpretResponse,
    ItemAllocationSchema,
    ParticipantAllocationSchema
)
from app.prompts.split_prompts import SPLIT_SYSTEM_PROMPT, build_split_prompt

class SplitService:
    """
    Interprets natural language expense splitting instructions into structured allocations.
    Validates all participant IDs against authorized group members.
    """

    async def interpret_split(self, req: SplitInterpretRequest) -> SplitInterpretResponse:
        valid_member_ids: Set[int] = {m.id for m in req.group_members}
        member_name_to_id: Dict[str, int] = {m.name.lower().strip(): m.id for m in req.group_members}

        # Guard: Check for unsupported foreign currency in natural language instruction
        foreign_currency_patterns = [
            (r'[\$]|(\b(usd|dollars?|bucks)\b)', "USD"),
            (r'[€]|(\b(eur|euros?)\b)', "EUR"),
            (r'[£]|(\b(gbp|pounds?)\b)', "GBP"),
            (r'[¥]|(\b(jpy|yen)\b)', "JPY")
        ]
        for pattern, curr in foreign_currency_patterns:
            if re.search(pattern, req.instruction, re.IGNORECASE):
                logger.info(f"Natural language instruction contains unsupported foreign currency ({curr}): {req.instruction}")
                return SplitInterpretResponse(
                    original_instruction=req.instruction,
                    description=None,
                    total_amount=None,
                    payer_id=req.payer_id,
                    split_type="EQUAL",
                    allocations=[],
                    participant_allocations=[],
                    unresolved_references=[],
                    clarification_required=True,
                    clarification_question=f"Foreign currency ({curr}) detected. Splitwise AI currently only supports INR (₹) transactions. Please convert the amount to INR before splitting.",
                    explanation=f"Unsupported currency ({curr}) detected in instruction. The group ledger operates strictly in INR (₹). Foreign amounts cannot be silently posted.",
                    confidence=0.0
                )

        try:
            # Build prompt
            prompt = build_split_prompt(
                instruction=req.instruction,
                members=[m.model_dump() for m in req.group_members],
                total_amount=float(req.total_amount or 0.0),
                items=[it.model_dump() for it in req.items] if req.items else [],
                payer_id=req.payer_id
            )

            raw_res = await ollama_provider.generate_structured(
                prompt=prompt,
                system_prompt=SPLIT_SYSTEM_PROMPT
            )

            return self._validate_and_sanitize(raw_res, req, valid_member_ids, member_name_to_id)

        except Exception as e:
            logger.warning(f"Ollama split interpretation failed or unavailable: {e}. Using deterministic heuristic parser.")
            return self._fallback_heuristic_parser(req, valid_member_ids, member_name_to_id)

    def _validate_and_sanitize(
        self,
        data: Dict[str, Any],
        req: SplitInterpretRequest,
        valid_member_ids: Set[int],
        member_name_to_id: Dict[str, int]
    ) -> SplitInterpretResponse:
        allocations_raw = data.get("allocations", [])
        unresolved: List[str] = list(data.get("unresolved_references", []))
        clarification_required: bool = bool(data.get("clarification_required", False))
        clarification_question: Optional[str] = data.get("clarification_question")
        explanation: Optional[str] = data.get("explanation")
        description: Optional[str] = data.get("description")
        split_type: str = data.get("split_type", "EQUAL")

        total_amt_val = data.get("total_amount")
        total_amt = Decimal(str(total_amt_val)) if total_amt_val is not None else req.total_amount

        payer_id_val = data.get("payer_id")
        try:
            payer_id = int(payer_id_val) if (payer_id_val is not None and int(payer_id_val) in valid_member_ids) else req.payer_id
        except Exception:
            payer_id = req.payer_id

        member_lookup = {m.id: m.name for m in req.group_members}
        valid_allocations: List[ItemAllocationSchema] = []
        all_referenced_pids: Set[int] = set()

        for alloc in allocations_raw:
            raw_pids = alloc.get("participant_ids", [])
            sanitized_pids: List[int] = []

            for pid in raw_pids:
                if isinstance(pid, int) and pid in valid_member_ids:
                    sanitized_pids.append(pid)
                    all_referenced_pids.add(pid)
                elif isinstance(pid, str) and pid.isdigit() and int(pid) in valid_member_ids:
                    sanitized_pids.append(int(pid))
                    all_referenced_pids.add(int(pid))
                else:
                    unresolved.append(f"Unknown participant ID: {pid}")

            if sanitized_pids:
                valid_allocations.append(ItemAllocationSchema(
                    item_id=str(alloc.get("item_id")) if alloc.get("item_id") else None,
                    item_description=alloc.get("item_description", description or "Expense"),
                    participant_ids=sanitized_pids,
                    split_type=alloc.get("split_type", split_type)
                ))

        # Check participant_allocations provided directly in LLM response
        participant_allocations: List[ParticipantAllocationSchema] = []
        raw_parts = data.get("participant_allocations", [])
        if raw_parts and isinstance(raw_parts, list):
            for rp in raw_parts:
                try:
                    uid = int(rp.get("user_id"))
                    if uid in valid_member_ids:
                        all_referenced_pids.add(uid)
                        pct = Decimal(str(rp.get("percent"))) if rp.get("percent") is not None else None
                        sa = Decimal(str(rp.get("share_amount"))) if rp.get("share_amount") is not None else None
                        if sa is None and pct is not None and total_amt:
                            sa = (total_amt * pct / Decimal("100")).quantize(Decimal("0.01"))
                        elif pct is None and sa is not None and total_amt and total_amt > 0:
                            pct = ((sa / total_amt) * Decimal("100")).quantize(Decimal("0.01"))
                        participant_allocations.append(ParticipantAllocationSchema(
                            user_id=uid,
                            user_name=member_lookup.get(uid, f"User {uid}"),
                            share_amount=sa,
                            percent=pct
                        ))
                except Exception:
                    pass

        # Check if unresolved entities require clarification
        if unresolved:
            clarification_required = True
            if not clarification_question:
                clarification_question = f"Could not recognize participants: {', '.join(unresolved)}. Which group members do they refer to?"

        # Fallback if participant_allocations was empty
        if not participant_allocations:
            if not all_referenced_pids:
                all_referenced_pids = valid_member_ids
            n = len(all_referenced_pids)
            approx_share = (total_amt / Decimal(str(n))).quantize(Decimal("0.01")) if (total_amt and n > 0) else Decimal("0.00")
            for uid in all_referenced_pids:
                participant_allocations.append(ParticipantAllocationSchema(
                    user_id=uid,
                    user_name=member_lookup.get(uid, f"User {uid}"),
                    share_amount=approx_share
                ))

        if not valid_allocations:
            valid_allocations.append(ItemAllocationSchema(
                item_id=None,
                item_description=description or "Overall Expense",
                participant_ids=list(all_referenced_pids),
                split_type=split_type
            ))

        return SplitInterpretResponse(
            original_instruction=req.instruction,
            description=description,
            total_amount=total_amt,
            payer_id=payer_id,
            split_type=split_type,
            allocations=valid_allocations,
            participant_allocations=participant_allocations,
            unresolved_references=list(set(unresolved)),
            clarification_required=clarification_required,
            clarification_question=clarification_question,
            explanation=explanation,
            confidence=0.95 if not unresolved else 0.70
        )

    def _fallback_heuristic_parser(
        self,
        req: SplitInterpretRequest,
        valid_member_ids: Set[int],
        member_name_to_id: Dict[str, int]
    ) -> SplitInterpretResponse:
        """
        Deterministic regex/keyword based allocation parser for testing and when LLM is unavailable.
        """
        instruction_lower = req.instruction.lower()
        member_lookup = {m.id: m.name for m in req.group_members}

        # Extract amount if present in instruction (e.g. ₹1,200 or 1200 or 1200.00)
        amt_match = re.search(r"(?:₹|rs\.?|\$)\s*([0-9,]+(?:\.[0-9]{1,2})?)", req.instruction, re.IGNORECASE)
        if not amt_match:
            amt_match = re.search(r"\b([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:rupees|rs|dollars)\b", req.instruction, re.IGNORECASE)
        total_amt = req.total_amount
        if amt_match:
            try:
                total_amt = Decimal(amt_match.group(1).replace(",", ""))
            except Exception:
                pass

        # Extract description (e.g. "for dinner", "for groceries", "for lunch")
        desc_match = re.search(r"for\s+([a-zA-Z\s]+?)(?:\.|$|,|\bshould\b|\bexcluding\b)", req.instruction, re.IGNORECASE)
        description = desc_match.group(1).strip().capitalize() if desc_match else "Dinner"

        # Extract payer (e.g. "Alex paid" -> Alex Morgan)
        payer_id = req.payer_id
        for name_clean, uid in member_name_to_id.items():
            first = name_clean.split()[0]
            if f"{first} paid" in instruction_lower or f"{name_clean} paid" in instruction_lower:
                payer_id = uid
                break

        # Check for explicit percentages per member (e.g. "Alex should pay 50%, Alice 25%, and Bob 25%")
        percent_allocs = {}
        for name_clean, uid in member_name_to_id.items():
            first = name_clean.split()[0]
            p_match = re.search(rf"\b{first}\b[a-zA-Z\s]*?([0-9]{{1,3}})\s*%", req.instruction, re.IGNORECASE)
            if p_match:
                percent_allocs[uid] = Decimal(p_match.group(1))

        # Check for "exclude <name>" or "except <name>"
        excluded_uids = set()
        ex_match = re.search(r"(?:exclude|except)\s+([a-zA-Z\s,]+)", instruction_lower)
        if ex_match:
            ex_target = ex_match.group(1)
            for name_clean, uid in member_name_to_id.items():
                first = name_clean.split()[0]
                if first in ex_target or name_clean in ex_target:
                    excluded_uids.add(uid)

        p_allocs: List[ParticipantAllocationSchema] = []
        split_type = "EQUAL"

        if percent_allocs:
            split_type = "PERCENT"
            for uid, pct in percent_allocs.items():
                if uid not in excluded_uids:
                    sa = (total_amt * pct / Decimal("100")).quantize(Decimal("0.01")) if total_amt else Decimal("0.00")
                    p_allocs.append(ParticipantAllocationSchema(
                        user_id=uid,
                        user_name=member_lookup.get(uid, f"User {uid}"),
                        share_amount=sa,
                        percent=pct
                    ))
        else:
            matched_user_ids = set()
            for name_clean, uid in member_name_to_id.items():
                first = name_clean.split()[0]
                if (first in instruction_lower or name_clean in instruction_lower) and uid not in excluded_uids:
                    matched_user_ids.add(uid)

            if not matched_user_ids:
                matched_user_ids = set(valid_member_ids) - excluded_uids
            if not matched_user_ids:
                matched_user_ids = set(valid_member_ids)

            n = len(matched_user_ids)
            approx_share = (total_amt / Decimal(str(n))).quantize(Decimal("0.01")) if (total_amt and n > 0) else Decimal("0.00")
            for uid in matched_user_ids:
                p_allocs.append(ParticipantAllocationSchema(
                    user_id=uid,
                    user_name=member_lookup.get(uid, f"User {uid}"),
                    share_amount=approx_share
                ))

        active_pids = [p.user_id for p in p_allocs]
        allocations = [ItemAllocationSchema(
            item_id=None,
            item_description=description,
            participant_ids=active_pids,
            split_type=split_type
        )]

        return SplitInterpretResponse(
            original_instruction=req.instruction,
            description=description,
            total_amount=total_amt,
            payer_id=payer_id,
            split_type=split_type,
            allocations=allocations,
            participant_allocations=p_allocs,
            unresolved_references=[],
            clarification_required=False,
            clarification_question=None,
            explanation=f"Parsed {description} expense: Total ₹{total_amt or 0.00}, paid by {member_lookup.get(payer_id, 'Member')}, split {split_type}.",
            confidence=0.95
        )

split_service = SplitService()
