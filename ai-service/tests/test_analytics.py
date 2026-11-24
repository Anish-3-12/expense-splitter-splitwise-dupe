from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-Internal-Secret": "splitwise-ai-internal-secret-2026"}

def test_anomaly_detection_insufficient_data():
    payload = {
        "group_id": 1,
        "historical_expenses": [
            {"expense_id": 1, "amount": 100.0, "payer_id": 1},
            {"expense_id": 2, "amount": 150.0, "payer_id": 2}
        ]
    }
    response = client.post("/internal/v1/analytics/detect-anomalies", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["method_used"] == "INSUFFICIENT_DATA"
    for r in data["results"]:
        assert r["status"] == "INSUFFICIENT_DATA"

def test_anomaly_detection_statistical_iqr():
    # 7 normal transactions around 100-200, one massive spike of 2500
    expenses = [
        {"expense_id": 1, "amount": 120.0, "payer_id": 1},
        {"expense_id": 2, "amount": 150.0, "payer_id": 1},
        {"expense_id": 3, "amount": 180.0, "payer_id": 2},
        {"expense_id": 4, "amount": 140.0, "payer_id": 2},
        {"expense_id": 5, "amount": 130.0, "payer_id": 1},
        {"expense_id": 6, "amount": 160.0, "payer_id": 2},
        {"expense_id": 7, "amount": 2500.0, "payer_id": 1} # Outlier
    ]
    payload = {"group_id": 1, "historical_expenses": expenses}
    response = client.post("/internal/v1/analytics/detect-anomalies", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["method_used"] == "STATISTICAL_IQR"
    res_dict = {r["expense_id"]: r["status"] for r in data["results"]}
    assert res_dict[7] in ["UNUSUAL", "REQUIRES_REVIEW"]
    assert res_dict[1] == "NORMAL"

def test_anomaly_detection_isolation_forest():
    # 12 historical transactions around 100-200, one massive outlier of 5000
    expenses = [
        {"expense_id": i, "amount": 100.0 + (i * 10), "payer_id": 1}
        for i in range(1, 12)
    ]
    expenses.append({"expense_id": 99, "amount": 5000.0, "payer_id": 1})
    payload = {"group_id": 1, "historical_expenses": expenses}
    response = client.post("/internal/v1/analytics/detect-anomalies", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["method_used"] == "ISOLATION_FOREST"
    res_dict = {r["expense_id"]: r["status"] for r in data["results"]}
    assert res_dict[99] in ["UNUSUAL", "REQUIRES_REVIEW"]
