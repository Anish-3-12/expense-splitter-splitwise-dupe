from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-Internal-Secret": "splitwise-ai-internal-secret-2026"}

def test_categorize_merchant_rule():
    payload = {"merchant": "Swiggy Order", "note": "Dinner", "amount": 450.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Food & Dining"
    assert data["method"] == "RULE"

def test_categorize_uber():
    payload = {"merchant": "Uber India", "note": "Ride to airport", "amount": 620.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Transportation"

def test_categorize_groceries_keyword():
    payload = {"merchant": None, "note": "Bought milk, eggs and bread", "amount": 180.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Groceries"

def test_unauthorized_categorize():
    payload = {"merchant": "Uber"}
    response = client.post("/internal/v1/expenses/categorize", json=payload)
    assert response.status_code == 401

def test_categorize_apartment_rent():
    payload = {"merchant": None, "note": "November Apartment Rent", "amount": 2400.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Housing & Rent"

def test_categorize_suv_rental_distinguished_from_housing():
    payload = {"merchant": None, "note": "AWD SUV Rental & Snow Chains", "amount": 320.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Travel"
    assert data["category"] != "Housing & Rent"

def test_categorize_car_rental_distinguished_from_housing():
    payload = {"merchant": None, "note": "Airport Car Rental 3 days", "amount": 180.00}
    response = client.post("/internal/v1/expenses/categorize", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Travel"
    assert data["category"] != "Housing & Rent"
