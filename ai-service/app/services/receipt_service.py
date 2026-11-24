import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from app.core.logging import logger
from app.providers.ollama_provider import ollama_provider
from app.services.ocr_service import ocr_service
from app.schemas.receipt import ReceiptExtractRequest, ReceiptExtractResponse, ReceiptItemSchema
from app.prompts.receipt_prompts import RECEIPT_SYSTEM_PROMPT, build_receipt_prompt

RECEIPT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "merchant": {"type": "string"},
        "receipt_date": {"type": ["string", "null"]},
        "currency": {"type": "string"},
        "currency_symbol": {"type": "string"},
        "currency_evidence": {"type": "string"},
        "subtotal": {"type": ["number", "null"]},
        "tax": {"type": ["number", "null"]},
        "discounts": {"type": ["number", "null"]},
        "other_charges": {"type": ["number", "null"]},
        "total": {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "line_total": {"type": "number"}
                },
                "required": ["description", "quantity", "unit_price", "line_total"]
            }
        }
    },
    "required": ["merchant", "total", "items"]
}

def to_minor_units(amount: Optional[Decimal]) -> Optional[int]:
    """
    Converts a Decimal currency amount to integer minor units (paise / cents).
    Eliminates floating-point rounding errors during financial reconciliation.
    """
    if amount is None:
        return None
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def extract_subtotal(raw_text: str, model_subtotal: Optional[Decimal] = None) -> Optional[Decimal]:
    """
    Extracts subtotal from raw OCR text or validates model-extracted subtotal.
    Prioritizes explicit Subtotal lines. If missing, returns None.
    NEVER silently copies the final total into the subtotal field.
    """
    text = raw_text or ""
    # Pattern 1: Subtotal / Sub-total / Sub Total [$]25.97
    m1 = re.search(r"\bSub[\s-]?total\b[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m1:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m1.group(1)))
        except Exception:
            pass

    # Pattern 2: Net Amount / Net Total
    m2 = re.search(r"\bNet[\s-]*(?:Amount|Total)\b[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m2:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m2.group(1)))
        except Exception:
            pass

    if model_subtotal is not None and model_subtotal > Decimal("0.00"):
        return model_subtotal

    return None

def extract_tax(raw_text: str, model_tax: Optional[Decimal] = None) -> Decimal:
    """
    Extracts tax from raw OCR text or validates model tax.
    """
    if model_tax is not None and model_tax > Decimal("0.00"):
        return model_tax

    text = raw_text or ""
    m = re.search(r"\bTax(?:\s*\([^)]*\))?[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m.group(1)))
        except Exception:
            pass

    m_vat = re.search(r"\b(?:GST|CGST|SGST|VAT)[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m_vat:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m_vat.group(1)))
        except Exception:
            pass

    return Decimal("0.00")

def extract_discounts(raw_text: str, model_discounts: Optional[Decimal] = None) -> Decimal:
    """
    Extracts explicit discounts, coupons, savings, or promotions from OCR text.
    """
    if model_discounts is not None and model_discounts > Decimal("0.00"):
        return model_discounts

    text = raw_text or ""
    m = re.search(r"\b(?:Discount|Coupon|Promo|Savings?|Special Offer)\b[\s:$]*-?([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m.group(1)))
        except Exception:
            pass
    return Decimal("0.00")

def extract_other_charges(raw_text: str, model_charges: Optional[Decimal] = None) -> Decimal:
    """
    Extracts service charges, delivery fees, tips, or gratuities from OCR text.
    """
    if model_charges is not None and model_charges > Decimal("0.00"):
        return model_charges

    text = raw_text or ""
    m = re.search(r"\b(?:Service Charge|Delivery Fee|Convenience Fee|Tip|Gratuity)\b[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m.group(1)))
        except Exception:
            pass
    return Decimal("0.00")

def extract_total(raw_text: str, model_total: Optional[Decimal] = None) -> Decimal:
    """
    Extracts the final receipt total.
    """
    if model_total is not None and model_total > Decimal("0.00"):
        return model_total

    text = raw_text or ""
    m = re.search(r"\b(?:Total Amount|Grand Total|Total Due|Total)[\s:$]*([₹$€£]?\s*\d+(?:\.\d{1,2})?)", text, re.I)
    if m:
        try:
            return Decimal(re.sub(r"[^\d.]", "", m.group(1)))
        except Exception:
            pass
    return Decimal("0.00")

def validate_receipt_financial_invariants(
    items: List[ReceiptItemSchema],
    subtotal: Optional[Decimal],
    tax: Optional[Decimal],
    discounts: Optional[Decimal],
    other_charges: Optional[Decimal],
    total: Optional[Decimal],
    currency_symbol: str = "$"
) -> Tuple[str, Decimal, List[str], bool, bool, bool]:
    """
    Performs integer minor-unit financial reconciliation across two independent invariants:
    Invariant 1: sum(line_items) == subtotal
    Invariant 2: subtotal + tax + other_charges - discounts == total

    Returns:
    (validation_status, discrepancy_amount, warnings, inv1_passed, inv2_passed, is_ambiguous)
    """
    warnings: List[str] = []

    calc_total = sum((it.line_total for it in items), Decimal("0.00"))
    item_sum_minor = to_minor_units(calc_total) or 0
    subtotal_minor = to_minor_units(subtotal)
    tax_minor = to_minor_units(tax) or 0
    discounts_minor = to_minor_units(discounts) or 0
    other_charges_minor = to_minor_units(other_charges) or 0
    total_minor = to_minor_units(total)

    # Invariant 1: sum(line_items) == subtotal
    inv1_passed = False
    diff1_minor = 0
    if subtotal_minor is not None:
        diff1_minor = abs(item_sum_minor - subtotal_minor)
        inv1_passed = (diff1_minor == 0)
        if not inv1_passed:
            warnings.append(
                f"DISCREPANCY DETECTED: INVARIANT 1 FAILED: Sum of line items ({currency_symbol}{Decimal(item_sum_minor)/100:.2f}) "
                f"does not match receipt subtotal ({currency_symbol}{Decimal(subtotal_minor)/100:.2f}). "
                f"Discrepancy: {currency_symbol}{Decimal(diff1_minor)/100:.2f}."
            )
    else:
        inv1_passed = False
        warnings.append("DISCREPANCY DETECTED: Receipt subtotal could not be extracted; line items could not be verified against subtotal.")

    # Invariant 2: subtotal + tax + other_charges - discounts == total
    inv2_passed = False
    diff2_minor = 0
    if subtotal_minor is not None and total_minor is not None and total_minor > 0:
        expected_total_minor = subtotal_minor + tax_minor + other_charges_minor - discounts_minor
        diff2_minor = abs(expected_total_minor - total_minor)
        inv2_passed = (diff2_minor == 0)
        if not inv2_passed:
            warnings.append(
                f"DISCREPANCY DETECTED: INVARIANT 2 FAILED: Subtotal ({currency_symbol}{Decimal(subtotal_minor)/100:.2f}) "
                f"+ Tax ({currency_symbol}{Decimal(tax_minor)/100:.2f}) "
                f"+ Other charges ({currency_symbol}{Decimal(other_charges_minor)/100:.2f}) "
                f"- Discounts ({currency_symbol}{Decimal(discounts_minor)/100:.2f}) "
                f"= {currency_symbol}{Decimal(expected_total_minor)/100:.2f}, "
                f"which does not match final total ({currency_symbol}{Decimal(total_minor)/100:.2f}). "
                f"Discrepancy: {currency_symbol}{Decimal(diff2_minor)/100:.2f}."
            )
    else:
        inv2_passed = False
        warnings.append("Missing subtotal or final total; grand total arithmetic reconciliation could not be verified.")

    has_ambiguity = any(it.is_ambiguous for it in items)
    if has_ambiguity:
        ambig_descs = [it.description for it in items if it.is_ambiguous]
        warnings.append(f"Ambiguous items detected: {', '.join(ambig_descs)}. Please review unit price vs line total interpretations.")

    # RECONCILED requires BOTH invariants to pass and ZERO ambiguity
    if inv1_passed and inv2_passed and not has_ambiguity:
        validation_status = "RECONCILED"
        discrepancy_amount = Decimal("0.00")
    else:
        validation_status = "DISCREPANCY_DETECTED"
        discrepancy_amount = (Decimal(diff1_minor + diff2_minor) / 100).quantize(Decimal("0.01"))

    is_ambiguous = has_ambiguity or (validation_status != "RECONCILED")

    return validation_status, discrepancy_amount, warnings, inv1_passed, inv2_passed, is_ambiguous

def detect_currency(raw_text: str, model_currency: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Deterministically identifies currency from raw OCR text symbols and context.
    Never assumes INR when receipts clearly contain other currency signs.
    """
    text = raw_text or ""
    
    # Check for symbols and explicit country/currency tokens
    has_dollar = "$" in text or bool(re.search(r"\b(USD|Austin|Texas|TX|CA|NY|WA|FL|USA)\b", text, re.I))
    has_euro = "€" in text or bool(re.search(r"\b(EUR|Euro|Euros)\b", text, re.I))
    has_pound = "£" in text or bool(re.search(r"\b(GBP|Pound|Pounds)\b", text, re.I))
    has_rupee = "₹" in text or bool(re.search(r"\b(INR|Rs\.?|Rupees?|GSTIN)\b", text, re.I))

    if has_dollar and not has_rupee:
        return "USD", "$", "Detected '$' currency symbol and US location cues in OCR text"
    elif has_euro and not has_rupee:
        return "EUR", "€", "Detected '€' (Euro) currency symbol in OCR text"
    elif has_pound and not has_rupee:
        return "GBP", "£", "Detected '£' (Pound) currency symbol in OCR text"
    elif has_rupee and not has_dollar:
        return "INR", "₹", "Detected '₹' / INR currency symbol in OCR text"
    
    # If model suggested a valid currency that aligns with symbols
    if model_currency:
        mc = model_currency.upper().strip()
        if mc in ["USD", "$"]:
            return "USD", "$", "Model identified USD currency"
        elif mc in ["EUR", "€"]:
            return "EUR", "€", "Model identified EUR currency"
        elif mc in ["GBP", "£"]:
            return "GBP", "£", "Model identified GBP currency"
        elif mc in ["INR", "₹", "RS"]:
            return "INR", "₹", "Model identified INR currency"

    # If ambiguous, check if dollar symbol present
    if "$" in text:
        return "USD", "$", "Detected '$' symbol"
    if "₹" in text or "Rs" in text:
        return "INR", "₹", "Detected '₹' symbol"
    if "€" in text:
        return "EUR", "€", "Detected '€' symbol"
    if "£" in text:
        return "GBP", "£", "Detected '£' symbol"

    return "USD", "$", "Defaulted to USD based on document structure (no specific currency symbol detected)"

def extract_receipt_date(raw_text: str, model_date: Optional[str] = None) -> Optional[str]:
    """
    Extracts and standardizes receipt date to YYYY-MM-DD from OCR text.
    Prefers deterministic regex match from raw OCR text over LLM hallucinated dates.
    """
    text = raw_text or ""
    # Pattern 1: Date: YYYY-MM-DD or YYYY/MM/DD
    m1 = re.search(r"(?:Date|Dated)[\s:]*([12]\d{3})[-/.](1[0-2]|0?[1-9])[-/.]([12]\d|3[01]|0?[1-9])\b", text, re.I)
    if m1:
        return f"{m1.group(1)}-{int(m1.group(2)):02d}-{int(m1.group(3)):02d}"

    # Pattern 2: Standalone ISO date YYYY-MM-DD
    m2 = re.search(r"\b([12]\d{3})[-/.](1[0-2]|0?[1-9])[-/.]([12]\d|3[01]|0?[1-9])\b", text)
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"

    # Pattern 3: MM/DD/YYYY e.g. 11/15/2026
    m3 = re.search(r"\b(1[0-2]|0?[1-9])[-/.]([12]\d|3[01]|0?[1-9])[-/.]([12]\d{3})\b", text)
    if m3:
        return f"{m3.group(3)}-{int(m3.group(1)):02d}-{int(m3.group(2)):02d}"

    if model_date and re.match(r"^\d{4}-\d{2}-\d{2}$", str(model_date).strip()):
        return str(model_date).strip()

    return None

class ReceiptService:
    """
    Coordinates receipt OCR extraction and Ollama structured interpretation with
    robust currency detection, date parsing, unit price vs line total reconciliation,
    and discrepancy reporting.
    """

    async def process_receipt(self, req: ReceiptExtractRequest) -> ReceiptExtractResponse:
        raw_text = req.raw_ocr_text
        if not raw_text and req.file_path:
            raw_text, _ = ocr_service.extract_text(req.file_path)

        if not raw_text or not raw_text.strip():
            raw_text = "Empty Receipt"

        try:
            # Query Ollama for structured interpretation using strict grammar schema
            prompt = build_receipt_prompt(raw_text)
            structured_data = await ollama_provider.generate_structured(
                prompt=prompt,
                response_schema=RECEIPT_RESPONSE_SCHEMA,
                system_prompt=RECEIPT_SYSTEM_PROMPT
            )
            return self._build_validated_response(structured_data, raw_text)

        except Exception as e:
            logger.warning(f"Ollama receipt interpretation failed, using rule-based fallback parser: {e}")
            return self._fallback_rule_parser(raw_text)

    def _build_validated_response(self, data: Dict[str, Any], raw_text: str) -> ReceiptExtractResponse:
        merchant = data.get("merchant") or "Unknown Merchant"

        # Deterministic currency & date
        currency, currency_symbol, currency_evidence = detect_currency(raw_text, data.get("currency"))
        receipt_date = extract_receipt_date(raw_text, data.get("receipt_date"))

        # Explicit subtotal from OCR or model (Never silently copied from total)
        model_subtotal = Decimal(str(data.get("subtotal"))) if (data.get("subtotal") is not None and str(data.get("subtotal")).strip() != "") else None
        subtotal = extract_subtotal(raw_text, model_subtotal)

        # Tax
        model_tax = Decimal(str(data.get("tax"))) if (data.get("tax") is not None and str(data.get("tax")).strip() != "") else None
        tax = extract_tax(raw_text, model_tax)

        # Discounts & Other Charges
        model_disc = Decimal(str(data.get("discounts"))) if (data.get("discounts") is not None and str(data.get("discounts")).strip() != "") else None
        discounts = extract_discounts(raw_text, model_disc)

        model_charges = Decimal(str(data.get("other_charges"))) if (data.get("other_charges") is not None and str(data.get("other_charges")).strip() != "") else None
        other_charges = extract_other_charges(raw_text, model_charges)

        # Total
        model_tot = Decimal(str(data.get("total", "0.00"))) if (data.get("total") is not None and str(data.get("total")).strip() != "") else None
        total = extract_total(raw_text, model_tot)

        items_raw = data.get("items", [])
        items: List[ReceiptItemSchema] = []

        for it in items_raw:
            desc = it.get("description", "Item")
            # Skip summary lines mistakenly included as line items
            desc_clean = desc.lower().strip()
            if any(desc_clean.startswith(prefix) for prefix in ["subtotal", "total", "tax", "gst", "balance due", "payment method", "auth code", "change"]):
                continue

            qty = Decimal(str(it.get("quantity", "1.00")))
            unit_p = Decimal(str(it.get("unit_price", "0.00")))
            line_tot = Decimal(str(it.get("line_total", "0.00")))

            # If model omitted line_total or set it to 0
            if line_tot <= Decimal("0.00") and unit_p > Decimal("0.00"):
                line_tot = unit_p * qty

            # Detect ambiguous quantity/price interpretation
            is_ambig = False
            ambig_reason = None
            if qty > Decimal("1.00"):
                if unit_p == line_tot and line_tot > Decimal("0.00"):
                    is_ambig = True
                    ambig_reason = f"Printed price {currency_symbol}{line_tot} may represent row total rather than unit price"
                elif abs(unit_p * qty - line_tot) > Decimal("0.05"):
                    is_ambig = True
                    ambig_reason = f"Line total ({currency_symbol}{line_tot}) does not equal quantity ({qty}) * unit price ({currency_symbol}{unit_p})"

            items.append(ReceiptItemSchema(
                description=desc,
                quantity=qty,
                unit_price=unit_p,
                line_total=line_tot,
                confidence=Decimal("0.95"),
                is_ambiguous=is_ambig,
                ambiguity_reason=ambig_reason
            ))

        calc_total = sum((it.line_total for it in items), Decimal("0.00"))

        # Perform integer minor-unit financial reconciliation across two separate invariants
        validation_status, discrepancy_amount, warnings, inv1_passed, inv2_passed, is_ambig = validate_receipt_financial_invariants(
            items=items,
            subtotal=subtotal,
            tax=tax,
            discounts=discounts,
            other_charges=other_charges,
            total=total,
            currency_symbol=currency_symbol
        )

        return ReceiptExtractResponse(
            merchant=merchant,
            receipt_date=receipt_date,
            currency=currency,
            currency_symbol=currency_symbol,
            currency_evidence=currency_evidence,
            subtotal=subtotal,
            tax=tax,
            discounts=discounts,
            other_charges=other_charges,
            item_sum=calc_total,
            total=total,
            items=items,
            warnings=warnings,
            validation_status=validation_status,
            discrepancy_amount=discrepancy_amount,
            is_item_subtotal_reconciled=inv1_passed,
            is_grand_total_reconciled=inv2_passed,
            is_ambiguous=is_ambig,
            raw_ocr_text=raw_text
        )

    def _fallback_rule_parser(self, text: str) -> ReceiptExtractResponse:
        """
        Deterministic regex-based fallback parser when Ollama is unavailable.
        Maintains currency detection, date parsing, unit price vs line total logic, and discrepancy flags.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        merchant = lines[0][:50] if lines else "Receipt Document"

        # Deterministic currency & date
        currency, currency_symbol, currency_evidence = detect_currency(text)
        receipt_date = extract_receipt_date(text)

        subtotal = extract_subtotal(text)
        tax = extract_tax(text)
        discounts = extract_discounts(text)
        other_charges = extract_other_charges(text)
        total = extract_total(text)

        items: List[ReceiptItemSchema] = []

        # Look for line items matching "<Name> [Qty] [$]Price"
        for line in lines:
            if any(kw in line.lower() for kw in ["total", "subtotal", "tax", "gst", "visa", "auth", "item", "receipt", "tel:", "store"]):
                continue

            # First try pattern with explicit quantity column: "<Description> <Qty> <Price>"
            m_qty = re.search(r"^(.+?)\s+(\d+)\s+(?:[₹$€£]\s*)?(\d+(?:\.\d{1,2})?)(?:\s*[₹$€£])?$", line.strip())
            if m_qty:
                desc = m_qty.group(1).strip()
                qty = Decimal(m_qty.group(2))
                price = Decimal(m_qty.group(3))
            else:
                # Fallback to pattern without quantity column: "<Description> <Price>"
                m_noqty = re.search(r"^(.+?)\s+(?:[₹$€£]\s*)?(\d+(?:\.\d{1,2})?)(?:\s*[₹$€£])?$", line.strip())
                if m_noqty:
                    desc = m_noqty.group(1).strip()
                    qty = Decimal("1.00")
                    price = Decimal(m_noqty.group(2))
                else:
                    continue

            if len(desc) < 2 or price <= Decimal("0.00"):
                continue

            try:
                # Distinguish unit price from line total:
                # If quantity > 1, the printed price on receipt row is typically line total
                # e.g., "Artisan Sourdough Bread 2 $7.50" -> line total is 7.50, unit is 3.75
                if qty > Decimal("1.00"):
                    line_tot = price
                    unit_p = (price / qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    is_ambig = True
                    ambig_reason = f"Assuming row price {currency_symbol}{price} is line total (unit: {currency_symbol}{unit_p})"
                else:
                    line_tot = price
                    unit_p = price
                    is_ambig = False
                    ambig_reason = None

                items.append(ReceiptItemSchema(
                    description=desc,
                    quantity=qty,
                    unit_price=unit_p,
                    line_total=line_tot,
                    confidence=Decimal("0.85"),
                    is_ambiguous=is_ambig,
                    ambiguity_reason=ambig_reason
                ))
            except Exception:
                pass

        calc_total = sum((it.line_total for it in items), Decimal("0.00"))

        validation_status, discrepancy_amount, warnings, inv1_passed, inv2_passed, is_ambig = validate_receipt_financial_invariants(
            items=items,
            subtotal=subtotal,
            tax=tax,
            discounts=discounts,
            other_charges=other_charges,
            total=total,
            currency_symbol=currency_symbol
        )

        warnings.insert(0, "Rule-based fallback parser used. Please review extracted figures.")

        return ReceiptExtractResponse(
            merchant=merchant,
            receipt_date=receipt_date,
            currency=currency,
            currency_symbol=currency_symbol,
            currency_evidence=currency_evidence,
            subtotal=subtotal,
            tax=tax,
            discounts=discounts,
            other_charges=other_charges,
            item_sum=calc_total,
            total=total,
            items=items,
            warnings=warnings,
            validation_status=validation_status,
            discrepancy_amount=discrepancy_amount,
            is_item_subtotal_reconciled=inv1_passed,
            is_grand_total_reconciled=inv2_passed,
            is_ambiguous=is_ambig,
            raw_ocr_text=text
        )

receipt_service = ReceiptService()
