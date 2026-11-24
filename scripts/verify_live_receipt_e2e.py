import urllib.request
import json
import os

def req(url, data=None, headers=None, method=None):
    h = dict(headers or {})
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}

def main():
    print("=== STARTING LIVE END-TO-END RECEIPT ACCURACY & IDEMPOTENCY TEST ===")

    # 1. Register & Login
    email = "live_receipt_tester_2026@test.com"
    s_reg, _ = req("http://localhost:8080/api/auth/register", {"name": "Live Tester", "email": email, "password": "password123"})
    s_login, login_res = req("http://localhost:8080/api/auth/login", {"email": email, "password": "password123"})
    assert s_login == 200, f"Login failed: {login_res}"
    token = "Bearer " + login_res["token"]
    headers = {"Authorization": token}

    # 2. Get Profile & Create Group
    _, me = req("http://localhost:8080/api/auth/me", headers=headers)
    my_id = me["id"]
    _, grp = req("http://localhost:8080/api/groups", {"name": "WholeFoods Test Group", "description": "Testing receipt accuracy"}, headers=headers)
    group_id = grp["id"]
    print(f"User ID: {my_id}, Group ID: {group_id}")

    # 3. Multipart Upload sample_receipt.png
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open("sample_receipt.png", "rb") as f:
        img_bytes = f.read()

    part_header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_receipt.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("latin-1")
    part_footer = f"\r\n--{boundary}--\r\n".encode("latin-1")
    body = part_header + img_bytes + part_footer

    upload_headers = {"Authorization": token, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    s_up, receipt = req(f"http://localhost:8080/api/groups/{group_id}/receipts", data=body, headers=upload_headers)
    assert s_up == 200, f"Upload failed: {receipt}"
    receipt_id = receipt["id"]
    print(f"Receipt uploaded successfully. ID: {receipt_id}")

    # 4. Trigger Extract (Spring Boot -> FastAPI AI service -> Tesseract OCR -> Ollama qwen2.5:1.5b)
    print("Triggering OCR & AI extraction...")
    s_ext, extracted = req(f"http://localhost:8080/api/groups/{group_id}/receipts/{receipt_id}/extract", method="POST", headers=headers)
    assert s_ext == 200, f"Extraction failed: {extracted}"

    print(f"Merchant: {extracted.get('merchantName')}")
    print(f"Date: {extracted.get('receiptDate')}")
    print(f"Currency: {extracted.get('currency')} ({extracted.get('currencySymbol')})")
    print(f"Subtotal: {extracted.get('subtotal')}")
    print(f"Tax: {extracted.get('tax')}")
    print(f"Total Amount: {extracted.get('totalAmount')}")
    print(f"Validation Status: {extracted.get('validationStatus')}")
    print(f"Discrepancy Amount: {extracted.get('discrepancyAmount')}")
    print(f"Items Count: {len(extracted.get('items', []))}")
    for it in extracted.get("items", []):
        print(f"  * {it.get('description')} | qty={it.get('quantity')} | unit={it.get('unitPrice')} | total={it.get('lineTotal')}")

    # Verify Currency is USD (NOT INR)
    assert extracted.get("currency") == "USD", f"Expected USD but got {extracted.get('currency')}"
    # Verify Date is 2026-11-15 (NOT null)
    assert extracted.get("receiptDate") == "2026-11-15", f"Expected 2026-11-15 but got {extracted.get('receiptDate')}"
    # Verify Subtotal is 25.97 (NOT 28.11!)
    assert str(extracted.get("subtotal")) == "25.97", f"Expected subtotal 25.97 but got {extracted.get('subtotal')}"
    # Verify Tax is 2.14
    assert str(extracted.get("tax")) == "2.14", f"Expected tax 2.14 but got {extracted.get('tax')}"
    # Verify Total is 28.11
    assert str(extracted.get("totalAmount")) == "28.11", f"Expected total 28.11 but got {extracted.get('totalAmount')}"
    # Verify Reconciled
    assert extracted.get("validationStatus") == "RECONCILED", f"Expected RECONCILED but got {extracted.get('validationStatus')}"
    assert float(extracted.get("discrepancyAmount") or 0.0) == 0.0, f"Expected 0.0 discrepancy but got {extracted.get('discrepancyAmount')}"

    # Verify Item Sum in integer cents
    sum_items_cents = sum(int(round(float(it["lineTotal"]) * 100)) for it in extracted.get("items", []))
    subtotal_cents = int(round(float(extracted["subtotal"]) * 100))
    tax_cents = int(round(float(extracted["tax"]) * 100))
    total_cents = int(round(float(extracted["totalAmount"]) * 100))

    print(f"Invariant 1 (Sum Items == Subtotal): {sum_items_cents} == {subtotal_cents} -> {sum_items_cents == subtotal_cents}")
    print(f"Invariant 2 (Subtotal + Tax == Total): {subtotal_cents} + {tax_cents} == {total_cents} -> {(subtotal_cents + tax_cents) == total_cents}")
    assert sum_items_cents == subtotal_cents, f"Invariant 1 broken: items sum {sum_items_cents} != subtotal {subtotal_cents}"
    assert subtotal_cents + tax_cents == total_cents, f"Invariant 2 broken: subtotal+tax {subtotal_cents + tax_cents} != total {total_cents}"

    # 4b. Test Review Endpoint (Simulate a user reviewing/editing an item price and observing status change)
    print("Testing Review Endpoint financial recalculation...")
    review_body = {
        "merchantName": extracted.get("merchantName"),
        "receiptDate": extracted.get("receiptDate"),
        "currency": extracted.get("currency"),
        "subtotal": 25.97,
        "tax": 2.14,
        "totalAmount": 28.11,
        "items": extracted.get("items", [])
    }
    s_rev, reviewed = req(f"http://localhost:8080/api/groups/{group_id}/receipts/{receipt_id}/review", data=review_body, method="PUT", headers=headers)
    assert s_rev == 200, f"Review failed: {reviewed}"
    assert reviewed.get("validationStatus") == "RECONCILED", f"Expected RECONCILED after review, got {reviewed.get('validationStatus')}"
    assert str(reviewed.get("subtotal")) == "25.97", f"Expected subtotal 25.97 after review, got {reviewed.get('subtotal')}"
    print("Review Endpoint verified: successfully preserved subtotal and RECONCILED status.")

    # 5. First Confirmation -> Creates Expense
    confirm_body = {"payerId": my_id, "splitType": "EQUAL", "note": "Whole Foods Groceries"}
    s_conf1, exp1 = req(f"http://localhost:8080/api/groups/{group_id}/receipts/{receipt_id}/confirm", data=confirm_body, headers=headers)
    print(f"First Confirm HTTP Status: {s_conf1} (Expense ID: {exp1.get('id')})")
    assert s_conf1 == 200, f"Expected 200 for first confirmation, got {s_conf1}"

    # 6. Second Confirmation -> Must return HTTP 409 Conflict
    s_conf2, err2 = req(f"http://localhost:8080/api/groups/{group_id}/receipts/{receipt_id}/confirm", data=confirm_body, headers=headers)
    print(f"Second Confirm HTTP Status: {s_conf2} (Expected 409 Conflict)")
    print(f"Conflict response: {err2}")
    assert s_conf2 == 409, f"Expected 409 for repeated confirmation, got {s_conf2}"

    print("=== LIVE END-TO-END VERIFICATION COMPLETED WITH 100% SUCCESS ===")

if __name__ == "__main__":
    main()
