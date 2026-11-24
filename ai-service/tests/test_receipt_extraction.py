from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-Internal-Secret": "splitwise-ai-internal-secret-2026"}

def test_receipt_extraction_raw_text():
    raw_ocr = """
    Pizza Palace Restaurant
    Date: 2026-03-15
    Pizza Margherita 450.00
    Garlic Bread 150.00
    Coke 50.00
    Total: 650.00
    """
    payload = {"raw_ocr_text": raw_ocr}
    response = client.post("/internal/v1/receipts/extract", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert float(data["total"]) > 0
    assert len(data["items"]) >= 1
    assert "merchant" in data
