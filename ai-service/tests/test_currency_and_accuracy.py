import pytest
from decimal import Decimal
from app.services.receipt_service import receipt_service, detect_currency, extract_receipt_date
from app.schemas.receipt import ReceiptExtractRequest

SAMPLE_USD_RECEIPT = """WHOLE FOODS MARKET
Store #10425 - Austin, TX
Tel: (512) 555-0199
Date: 2026-11-15 Time: 14:32
Receipt #: 984128

ITEM QTY PRICE
Organic Whole Milk 1 Gal 1 $4.99
Artisan Sourdough Bread 2 $7.50
Fresh Strawberries 1 lb 1 $3.99
Greek Yogurt Honey 32 oz 1 $5.49
Avocados Hass Organic 4 $4.00
Subtotal $25.97
Tax (8.25%) $2.14
Total Amount $28.11

Payment Method: VISA **** 4242
Auth Code: 084129
THANK YOU FOR SHOPPING WITH US!
"""

SAMPLE_EUR_RECEIPT = """CARREFOUR EXPRESS
Paris, France
Date: 2026-10-12
Baguette Tradition 2 2.40 €
Fromage Comte 1 4.50 €
Lait Bio 1L 1 1.20 €
Total 8.10 €
Merci de votre visite
"""

SAMPLE_GBP_RECEIPT = """SAINSBURYS SUPERMARKET
London, UK
Date: 2026-09-05
Earl Grey Tea 1 £3.20
Shortbread Biscuits 2 £4.00
Subtotal £7.20
Total £7.20
"""

SAMPLE_INR_RECEIPT = """NATURE'S BASKET
Indiranagar, Bangalore
GSTIN: 29AAAAA0000A1Z5
Date: 2026-11-01
Atta 5kg 1 ₹245.00
Paneer 200g 2 ₹160.00
Subtotal ₹405.00
CGST 2.5% ₹10.12
SGST 2.5% ₹10.12
Total ₹425.24
"""

def test_detect_currency_usd():
    currency, symbol, evidence = detect_currency(SAMPLE_USD_RECEIPT)
    assert currency == "USD"
    assert symbol == "$"
    assert "dollar" in evidence.lower() or "$" in evidence

def test_detect_currency_eur():
    currency, symbol, evidence = detect_currency(SAMPLE_EUR_RECEIPT)
    assert currency == "EUR"
    assert symbol == "€"
    assert "euro" in evidence.lower() or "€" in evidence

def test_detect_currency_gbp():
    currency, symbol, evidence = detect_currency(SAMPLE_GBP_RECEIPT)
    assert currency == "GBP"
    assert symbol == "£"
    assert "pound" in evidence.lower() or "£" in evidence

def test_detect_currency_inr():
    currency, symbol, evidence = detect_currency(SAMPLE_INR_RECEIPT)
    assert currency == "INR"
    assert symbol == "₹"
    assert "inr" in evidence.lower() or "₹" in evidence

def test_never_assume_inr_on_dollar_receipt():
    # Explicit test: even if model mistakenly suggests INR, text with '$' overrides or detects USD
    currency, symbol, _ = detect_currency("$25.00 Grocery Item", model_currency="INR")
    assert currency == "USD"
    assert symbol == "$"

def test_extract_receipt_date_various_formats():
    assert extract_receipt_date("Date: 2026-11-15 Time: 14:32") == "2026-11-15"
    assert extract_receipt_date("Purchase Date 11/15/2026") == "2026-11-15"
    assert extract_receipt_date("Dated: 2026.05.20") == "2026-05-20"
    assert extract_receipt_date("No date here") is None

def test_sample_usd_receipt_fallback_parsing():
    resp = receipt_service._fallback_rule_parser(SAMPLE_USD_RECEIPT)

    # 1. Currency
    assert resp.currency == "USD"
    assert resp.currency_symbol == "$"
    assert resp.currency_evidence is not None

    # 2. Date
    assert resp.receipt_date == "2026-11-15"

    # 3. Raw OCR text preserved
    assert resp.raw_ocr_text == SAMPLE_USD_RECEIPT

    # 4. Totals and Items
    assert resp.total > Decimal("20.00")
    assert len(resp.items) >= 4

    # 5. Check Bread line item
    bread_items = [it for it in resp.items if "bread" in it.description.lower()]
    assert len(bread_items) == 1
    bread = bread_items[0]
    # Row was "Artisan Sourdough Bread 2 $7.50"
    # Line total should be $7.50, unit price $3.75, quantity 2
    assert bread.line_total == Decimal("7.50")
    assert bread.quantity == Decimal("2.00")
    assert bread.unit_price == Decimal("3.75")

    # 6. Check Avocado line item
    avocado_items = [it for it in resp.items if "avocado" in it.description.lower()]
    assert len(avocado_items) == 1
    avocado = avocado_items[0]
    # Row was "Avocados Hass Organic 4 $4.00"
    assert avocado.line_total == Decimal("4.00")
    assert avocado.quantity == Decimal("4.00")
    assert avocado.unit_price == Decimal("1.00")

@pytest.mark.anyio
async def test_discrepancy_detection_not_silently_mutated():
    # Simulated model output where line items sum does NOT match receipt subtotal
    raw_data = {
        "merchant": "Mismatched Store",
        "receipt_date": "2026-11-15",
        "currency": "USD",
        "subtotal": 25.97,
        "tax": 2.14,
        "total": 28.11,
        "items": [
            {"description": "Item A", "quantity": 1, "unit_price": 10.00, "line_total": 10.00},
            {"description": "Item B", "quantity": 2, "unit_price": 20.00, "line_total": 40.00}
        ]
    }
    # calc_total = 50.00 vs subtotal = 25.97
    resp = receipt_service._build_validated_response(raw_data, "Sample receipt with discrepancy $28.11")

    # Verify: discrepancy flagged, prices NOT silently altered
    assert resp.validation_status == "DISCREPANCY_DETECTED"
    assert resp.discrepancy_amount == Decimal("24.03") # 50.00 - 25.97
    assert resp.is_ambiguous is True
    assert any("DISCREPANCY DETECTED" in w for w in resp.warnings)
    # Check that item prices remained exactly as parsed (not silently mutated)
    assert resp.items[0].line_total == Decimal("10.00")
    assert resp.items[1].line_total == Decimal("40.00")
