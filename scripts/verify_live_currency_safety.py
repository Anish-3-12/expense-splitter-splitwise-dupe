import requests
import json
import sys

BASE_URL = "http://localhost:8080/api"
AI_URL = "http://localhost:8000/internal/v1"
INTERNAL_SECRET = "splitwise-ai-internal-secret-2026"

def run_tests():
    print("=== LIVE FOREIGN CURRENCY SAFETY & INVARIANT AUDIT ===")

    # 1. Setup Isolated QA User
    qa_email = "qa.currency.tester@splitwise.ai"
    qa_pass = "Password123!"
    reg_resp = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "QA Currency Auditor",
        "email": qa_email,
        "password": qa_pass
    })

    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": qa_email,
        "password": qa_pass
    })
    if login_resp.status_code != 200:
        print(f"FAILED: Login failed: {login_resp.status_code} {login_resp.text}")
        return False

    login_data = login_resp.json()
    token = login_data["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"Failed to get current user: {me_resp.status_code}"
    user_id = me_resp.json()["id"]
    print(f"[1/6] Authenticated QA User ID: {user_id}")

    # 2. Create Isolated QA Group
    g_resp = requests.post(f"{BASE_URL}/groups", json={
        "name": "QA Foreign Currency Isolation Group",
        "description": "Dedicated group for testing multi-currency boundaries"
    }, headers=headers)
    if g_resp.status_code != 200:
        print(f"FAILED: Group creation failed: {g_resp.status_code}")
        return False
    group_id = g_resp.json()["id"]
    print(f"[2/6] Created Isolated QA Group ID: {group_id}")

    # 3. Test Foreign Currency Expense Rejection (400 Bad Request)
    exp_usd = requests.post(f"{BASE_URL}/groups/{group_id}/expenses", json={
        "amount": 50.00,
        "currency": "USD",
        "payerId": user_id,
        "splitType": "EQUAL",
        "note": "Should be rejected"
    }, headers=headers)
    print(f"[3/6] USD Expense POST Status: {exp_usd.status_code} (Expected 400)")
    assert exp_usd.status_code == 400, f"Expected 400, got {exp_usd.status_code}"

    exp_eur = requests.post(f"{BASE_URL}/groups/{group_id}/expenses", json={
        "amount": 40.00,
        "currency": "EUR",
        "payerId": user_id,
        "splitType": "EQUAL"
    }, headers=headers)
    print(f"      EUR Expense POST Status: {exp_eur.status_code} (Expected 400)")
    assert exp_eur.status_code == 400, f"Expected 400, got {exp_eur.status_code}"

    # 4. Test Foreign Currency Settlement Rejection (400 Bad Request)
    settle_usd = requests.post(f"{BASE_URL}/groups/{group_id}/settlements", json={
        "amount": 25.00,
        "currency": "USD",
        "fromUserId": user_id,
        "toUserId": user_id,
        "note": "Foreign settlement attempt"
    }, headers=headers)
    print(f"[4/6] USD Settlement POST Status: {settle_usd.status_code} (Expected 400)")
    assert settle_usd.status_code == 400, f"Expected 400, got {settle_usd.status_code}"

    # 5. Test Receipt Currency Tampering & Foreign Receipt Confirmation (422 Unprocessable Entity)
    # Upload sample receipt image
    with open("sample_receipt.png", "rb") as f:
        upload_resp = requests.post(
            f"{BASE_URL}/groups/{group_id}/receipts",
            files={"file": ("sample_receipt.png", f, "image/png")},
            headers=headers
        )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.status_code}"
    receipt_id = upload_resp.json()["id"]
    print(f"[5/6] Uploaded test receipt ID: {receipt_id}")

    # Extract receipt (which identifies it as USD from sample_receipt.png)
    ext_resp = requests.post(f"{BASE_URL}/groups/{group_id}/receipts/{receipt_id}/extract", headers=headers)
    assert ext_resp.status_code == 200, f"Extract failed: {ext_resp.status_code}"
    ext_data = ext_resp.json()
    extracted_currency = ext_data.get("currency")
    print(f"      Extracted Receipt Currency: {extracted_currency} (Total: {ext_data.get('totalAmount')})")

    # A) Attempt to tamper currency during review (e.g. modify USD to INR) -> expect 400 Bad Request
    tamper_resp = requests.put(f"{BASE_URL}/groups/{group_id}/receipts/{receipt_id}/review", json={
        "merchantName": "Safeway",
        "currency": "INR",  # Tampering from USD to INR
        "totalAmount": 28.11,
        "subtotal": 25.97,
        "tax": 2.14
    }, headers=headers)
    print(f"      Currency Tampering (USD->INR) Review Status: {tamper_resp.status_code} (Expected 400)")
    assert tamper_resp.status_code == 400, f"Expected 400, got {tamper_resp.status_code}"

    # B) Attempt to confirm foreign currency receipt -> expect 422 Unprocessable Entity
    confirm_resp = requests.post(f"{BASE_URL}/groups/{group_id}/receipts/{receipt_id}/confirm", json={
        "payerId": user_id,
        "splitType": "EQUAL",
        "note": "Confirming USD receipt should fail"
    }, headers=headers)
    print(f"      Foreign Receipt Confirmation Status: {confirm_resp.status_code} (Expected 422)")
    assert confirm_resp.status_code == 422, f"Expected 422, got {confirm_resp.status_code}"

    # 6. Test Natural Language Foreign Currency Guard (clarification_required = True)
    nl_resp = requests.post(f"{AI_URL}/expenses/interpret-split", json={
        "instruction": "Alex paid $75 for dinner with Alice.",
        "group_members": [{"id": user_id, "name": "Alex"}],
        "payer_id": user_id
    }, headers={"X-Internal-Secret": INTERNAL_SECRET})
    assert nl_resp.status_code == 200, f"AI interpret failed: {nl_resp.status_code}"
    nl_data = nl_resp.json()
    print(f"[6/6] AI Natural Language Foreign Currency ($75) Intercepted:")
    print(f"      clarification_required: {nl_data.get('clarification_required')}")
    print(f"      clarification_question: {nl_data.get('clarification_question')}")
    assert nl_data.get("clarification_required") is True
    assert "USD" in nl_data.get("clarification_question", "")

    # 7. Financial Invariant Check: Verify NO unintended expenses or balance changes
    exp_list = requests.get(f"{BASE_URL}/groups/{group_id}/expenses", headers=headers).json()
    bal_list = requests.get(f"{BASE_URL}/groups/{group_id}/balances", headers=headers).json()
    print(f"=== INVARIANT VERIFICATION ===")
    print(f"Total expenses created in QA group: {len(exp_list)} (Expected 0)")
    assert len(exp_list) == 0, f"Expected 0 expenses, found {len(exp_list)}"

    net_balances = [b.get("netBalance", 0.0) for b in bal_list]
    print(f"Group Net Balances: {net_balances} (Expected all 0.00)")
    for b in net_balances:
        assert abs(b) < 0.001, f"Non-zero balance found: {b}"

    print("\n>>> ALL TARGETED LIVE FOREIGN CURRENCY TESTS PASSED SUCCESSFULLY! <<<")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
