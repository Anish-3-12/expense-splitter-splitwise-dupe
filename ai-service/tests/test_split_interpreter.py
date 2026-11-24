from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-Internal-Secret": "splitwise-ai-internal-secret-2026"}

def test_split_interpreter_basic():
    payload = {
        "instruction": "Rahul and I share the pizza. Everyone shares drinks.",
        "group_members": [
            {"id": 1, "name": "Rahul", "email": "rahul@example.com"},
            {"id": 2, "name": "Alice", "email": "alice@example.com"},
            {"id": 3, "name": "Bob", "email": "bob@example.com"}
        ],
        "total_amount": 600.00,
        "payer_id": 2,
        "items": [
            {"id": "item-1", "description": "Pizza", "amount": 400.00},
            {"id": "item-2", "description": "Drinks", "amount": 200.00}
        ]
    }
    response = client.post("/internal/v1/expenses/interpret-split", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "allocations" in data
    assert len(data["allocations"]) > 0

    # Ensure no fabricated user IDs
    valid_ids = {1, 2, 3}
    for alloc in data["allocations"]:
        for pid in alloc["participant_ids"]:
            assert pid in valid_ids

def test_split_interpreter_rejects_hallucinated_users():
    payload = {
        "instruction": "Split between Rahul and Elon Musk.",
        "group_members": [
            {"id": 10, "name": "Rahul", "email": "rahul@example.com"},
            {"id": 20, "name": "Priya", "email": "priya@example.com"}
        ],
        "total_amount": 500.00,
        "payer_id": 10
    }
    response = client.post("/internal/v1/expenses/interpret-split", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()

    # Elon Musk is not in group members; must not be assigned a fake ID
    valid_ids = {10, 20}
    for alloc in data["allocations"]:
        for pid in alloc["participant_ids"]:
            assert pid in valid_ids

def test_split_interpreter_foreign_currency_usd_requires_clarification():
    payload = {
        "instruction": "I paid $50 for dinner, split equally with Rahul.",
        "group_members": [
            {"id": 10, "name": "Rahul", "email": "rahul@example.com"},
            {"id": 20, "name": "Alex", "email": "alex@example.com"}
        ],
        "payer_id": 20
    }
    response = client.post("/internal/v1/expenses/interpret-split", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data.get("clarification_required") is True
    assert "USD" in data.get("clarification_question", "")
    assert "INR" in data.get("clarification_question", "")
    assert data.get("confidence") == 0.0
    assert len(data.get("allocations", [])) == 0
    assert data.get("total_amount") is None

def test_split_interpreter_foreign_currency_eur_requires_clarification():
    payload = {
        "instruction": "Rahul paid 100 EUR for train tickets. Split with me.",
        "group_members": [
            {"id": 10, "name": "Rahul", "email": "rahul@example.com"},
            {"id": 20, "name": "Alex", "email": "alex@example.com"}
        ],
        "payer_id": 10
    }
    response = client.post("/internal/v1/expenses/interpret-split", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data.get("clarification_required") is True
    assert "EUR" in data.get("clarification_question", "")
    assert data.get("confidence") == 0.0
    assert len(data.get("allocations", [])) == 0
