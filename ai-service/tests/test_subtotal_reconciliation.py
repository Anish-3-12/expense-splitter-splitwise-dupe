import pytest
from decimal import Decimal
from app.services.receipt_service import (
    receipt_service,
    extract_subtotal,
    extract_tax,
    extract_discounts,
    extract_other_charges,
    to_minor_units,
    validate_receipt_financial_invariants
)
from app.schemas.receipt import ReceiptItemSchema

# 1. Items $25.97 + tax $2.14 = total $28.11
def test_subtotal_reconciliation_exact_match():
    raw_data = {
        "merchant": "Whole Foods Market",
        "receipt_date": "2026-11-15",
        "currency": "USD",
        "subtotal": 25.97,
        "tax": 2.14,
        "total": 28.11,
        "items": [
            {"description": "Organic Whole Milk", "quantity": 1, "unit_price": 4.99, "line_total": 4.99},
            {"description": "Artisan Sourdough Bread", "quantity": 2, "unit_price": 3.75, "line_total": 7.50},
            {"description": "Fresh Strawberries", "quantity": 1, "unit_price": 3.99, "line_total": 3.99},
            {"description": "Greek Yogurt Honey", "quantity": 1, "unit_price": 5.49, "line_total": 5.49},
            {"description": "Avocados Hass Organic", "quantity": 4, "unit_price": 1.00, "line_total": 4.00}
        ]
    }
    raw_text = "WHOLE FOODS MARKET\nSubtotal $25.97\nTax $2.14\nTotal $28.11"
    resp = receipt_service._build_validated_response(raw_data, raw_text)

    assert resp.subtotal == Decimal("25.97")
    assert resp.total == Decimal("28.11")
    assert resp.tax == Decimal("2.14")
    assert resp.item_sum == Decimal("25.97")
    assert resp.validation_status == "RECONCILED"
    assert resp.discrepancy_amount == Decimal("0.00")
    assert resp.is_item_subtotal_reconciled is True
    assert resp.is_grand_total_reconciled is True
    assert resp.is_ambiguous is False
    assert len(resp.warnings) == 0

# 2. Incorrect subtotal of $28.11 must be flagged
def test_incorrect_subtotal_equal_to_total_flagged():
    raw_data = {
        "merchant": "Whole Foods Market",
        "receipt_date": "2026-11-15",
        "currency": "USD",
        "subtotal": 28.11, # Incorrectly set equal to total
        "tax": 2.14,
        "total": 28.11,
        "items": [
            {"description": "Organic Whole Milk", "quantity": 1, "unit_price": 4.99, "line_total": 4.99},
            {"description": "Artisan Sourdough Bread", "quantity": 2, "unit_price": 3.75, "line_total": 7.50},
            {"description": "Fresh Strawberries", "quantity": 1, "unit_price": 3.99, "line_total": 3.99},
            {"description": "Greek Yogurt Honey", "quantity": 1, "unit_price": 5.49, "line_total": 5.49},
            {"description": "Avocados Hass Organic", "quantity": 4, "unit_price": 1.00, "line_total": 4.00}
        ]
    }
    # Notice: items sum is $25.97, but subtotal claims $28.11
    resp = receipt_service._build_validated_response(raw_data, "WHOLE FOODS MARKET\nTotal $28.11")

    assert resp.validation_status == "DISCREPANCY_DETECTED"
    assert resp.is_item_subtotal_reconciled is False
    assert resp.is_grand_total_reconciled is False
    assert resp.discrepancy_amount > Decimal("0.00")
    assert any("INVARIANT 1 FAILED" in w for w in resp.warnings)

# 3. Correct subtotal with incorrect tax must be flagged
def test_correct_subtotal_with_incorrect_tax_flagged():
    raw_data = {
        "merchant": "Store",
        "currency": "USD",
        "subtotal": 25.97,
        "tax": 5.00, # Incorrect tax (25.97 + 5.00 = 30.97 != 28.11)
        "total": 28.11,
        "items": [
            {"description": "Item 1", "quantity": 1, "unit_price": 25.97, "line_total": 25.97}
        ]
    }
    resp = receipt_service._build_validated_response(raw_data, "Store\nSubtotal $25.97\nTax $5.00\nTotal $28.11")

    assert resp.is_item_subtotal_reconciled is True
    assert resp.is_grand_total_reconciled is False
    assert resp.validation_status == "DISCREPANCY_DETECTED"
    assert any("INVARIANT 2 FAILED" in w for w in resp.warnings)

# 4. Correct subtotal and tax with incorrect final total must be flagged
def test_correct_subtotal_and_tax_with_incorrect_final_total_flagged():
    raw_data = {
        "merchant": "Store",
        "currency": "USD",
        "subtotal": 25.97,
        "tax": 2.14,
        "total": 35.00, # Incorrect final total (25.97 + 2.14 = 28.11 != 35.00)
        "items": [
            {"description": "Item 1", "quantity": 1, "unit_price": 25.97, "line_total": 25.97}
        ]
    }
    resp = receipt_service._build_validated_response(raw_data, "Store\nSubtotal $25.97\nTax $2.14\nTotal $35.00")

    assert resp.is_item_subtotal_reconciled is True
    assert resp.is_grand_total_reconciled is False
    assert resp.validation_status == "DISCREPANCY_DETECTED"
    assert any("INVARIANT 2 FAILED" in w for w in resp.warnings)

# 5. Missing subtotal should remain unknown rather than being copied from total
def test_missing_subtotal_remains_unknown():
    raw_data = {
        "merchant": "No Subtotal Store",
        "currency": "USD",
        "subtotal": None, # Missing subtotal
        "tax": 2.14,
        "total": 28.11,
        "items": [
            {"description": "Item 1", "quantity": 1, "unit_price": 25.97, "line_total": 25.97}
        ]
    }
    raw_text = "No Subtotal Store\nItem 1 $25.97\nTotal $28.11"
    resp = receipt_service._build_validated_response(raw_data, raw_text)

    # Subtotal must NOT be copied from total
    assert resp.subtotal is None
    assert resp.total == Decimal("28.11")
    assert resp.validation_status != "RECONCILED"
    assert resp.is_item_subtotal_reconciled is False
    assert any("subtotal could not be extracted" in w.lower() for w in resp.warnings)

# 6. Ambiguous receipt values must not receive RECONCILED status
def test_ambiguous_values_never_reconciled():
    # Numbers add up, but an item is flagged ambiguous
    items = [
        ReceiptItemSchema(
            description="Ambiguous Bread",
            quantity=Decimal("2"),
            unit_price=Decimal("7.50"),
            line_total=Decimal("7.50"),
            is_ambiguous=True,
            ambiguity_reason="Possible unit price vs row total ambiguity"
        )
    ]
    status, disc, warnings, inv1, inv2, is_ambig = validate_receipt_financial_invariants(
        items=items,
        subtotal=Decimal("7.50"),
        tax=Decimal("0.50"),
        discounts=Decimal("0.00"),
        other_charges=Decimal("0.00"),
        total=Decimal("8.00"),
        currency_symbol="$"
    )

    assert inv1 is True
    assert inv2 is True
    # MUST NOT be RECONCILED due to ambiguity
    assert status != "RECONCILED"
    assert is_ambig is True
    assert any("Ambiguous items detected" in w for w in warnings)

# 7. A receipt with legitimate discounts or additional charges must be reconciled correctly
def test_receipt_with_legitimate_discounts_and_charges():
    # Subtotal: 100.00
    # Tax: 8.50
    # Service Charge: 5.00
    # Discount: 13.50
    # Total: 100.00 + 8.50 + 5.00 - 13.50 = 100.00
    items = [
        ReceiptItemSchema(description="Item A", quantity=Decimal("1"), unit_price=Decimal("60.00"), line_total=Decimal("60.00")),
        ReceiptItemSchema(description="Item B", quantity=Decimal("2"), unit_price=Decimal("20.00"), line_total=Decimal("40.00"))
    ]
    status, disc, warnings, inv1, inv2, is_ambig = validate_receipt_financial_invariants(
        items=items,
        subtotal=Decimal("100.00"),
        tax=Decimal("8.50"),
        discounts=Decimal("13.50"),
        other_charges=Decimal("5.00"),
        total=Decimal("100.00"),
        currency_symbol="$"
    )

    assert inv1 is True
    assert inv2 is True
    assert is_ambig is False
    assert status == "RECONCILED"
    assert disc == Decimal("0.00")
