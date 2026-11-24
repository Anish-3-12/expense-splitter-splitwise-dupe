import urllib.request
import json
import subprocess
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080/api"

def api(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8")
        try:
            return e.code, json.loads(text)
        except Exception:
            return e.code, {"raw": text}

def main():
    print("=== SEEDING REALISTIC DEMO DATA FOR SPLITWISE AI REVIEW ===")

    # 1. Create Users
    users_data = [
        {"name": "Alex Morgan", "email": "demo.reviewer@splitwise.ai", "password": "Password123!"},
        {"name": "Alice Chen", "email": "alice.chen@splitwise.ai", "password": "Password123!"},
        {"name": "Bob Martinez", "email": "bob.martinez@splitwise.ai", "password": "Password123!"},
        {"name": "Carol Taylor", "email": "carol.taylor@splitwise.ai", "password": "Password123!"},
        {"name": "David Kim", "email": "david.kim@splitwise.ai", "password": "Password123!"},
    ]

    user_tokens = {}
    user_ids = {}

    for u in users_data:
        code, res = api("/auth/register", method="POST", data=u)
        print(f"Register {u['name']}: {code}")
        # Login
        code, lres = api("/auth/login", method="POST", data={"email": u["email"], "password": u["password"]})
        if code == 200:
            user_tokens[u["email"]] = lres["token"]
            _, me = api("/auth/me", token=lres["token"])
            user_ids[u["email"]] = me["id"]
            print(f"Logged in {u['name']} (ID: {me['id']})")
        else:
            print(f"Failed to login {u['name']}: {lres}")

    alex_token = user_tokens["demo.reviewer@splitwise.ai"]
    alex_id = user_ids["demo.reviewer@splitwise.ai"]
    alice_id = user_ids["alice.chen@splitwise.ai"]
    bob_id = user_ids["bob.martinez@splitwise.ai"]
    carol_id = user_ids["carol.taylor@splitwise.ai"]
    david_id = user_ids["david.kim@splitwise.ai"]

    # 2. Get Categories
    _, cats = api("/categories", token=alex_token)
    cat_map = {c["name"].lower(): c["id"] for c in cats}
    print(f"Categories loaded: {list(cat_map.keys())}")

    # 3. Create 3 Groups
    groups = [
        {"name": "Apartment 4B Roommates", "members": [alice_id, bob_id, carol_id], "emails": ["alice.chen@splitwise.ai", "bob.martinez@splitwise.ai", "carol.taylor@splitwise.ai"]},
        {"name": "Lake Tahoe Ski Trip", "members": [alice_id, bob_id, david_id], "emails": ["alice.chen@splitwise.ai", "bob.martinez@splitwise.ai", "david.kim@splitwise.ai"]},
        {"name": "Weekend Foodies Club", "members": [bob_id, carol_id, david_id], "emails": ["bob.martinez@splitwise.ai", "carol.taylor@splitwise.ai", "david.kim@splitwise.ai"]}
    ]

    group_ids = []
    for g in groups:
        code, gres = api("/groups", method="POST", data={"name": g["name"]}, token=alex_token)
        gid = gres["id"]
        group_ids.append(gid)
        print(f"Created group '{g['name']}' with ID {gid}")
        # Add members
        for email in g["emails"]:
            code_m, mres = api(f"/groups/{gid}/members", method="POST", data={"email": email, "role": "MEMBER"}, token=alex_token)
            print(f"  Added {email} to group {gid}: {code_m}")

    gid1, gid2, gid3 = group_ids

    # 4. Create 18 Expenses
    rent_cat = cat_map.get("rent") or cat_map.get("housing")
    util_cat = cat_map.get("utilities")
    groc_cat = cat_map.get("groceries") or cat_map.get("food & drink")
    din_cat = cat_map.get("dining") or cat_map.get("food & drink")
    ent_cat = cat_map.get("entertainment")
    trav_cat = cat_map.get("travel") or cat_map.get("transportation")
    shop_cat = cat_map.get("shopping") or cat_map.get("general")

    expense_payloads = [
        # Group 1: Apartment 4B
        (gid1, {"amount": 2400.00, "payerId": alex_id, "splitType": "EQUAL", "currency": "USD", "note": "November Apartment Rent", "categoryId": rent_cat}),
        (gid1, {"amount": 80.00, "payerId": alice_id, "splitType": "EQUAL", "currency": "USD", "note": "Gigabit Fiber Internet", "categoryId": util_cat}),
        (gid1, {"amount": 145.50, "payerId": bob_id, "splitType": "EQUAL", "currency": "USD", "note": "Electric & Gas Heating", "categoryId": util_cat}),
        (gid1, {
            "amount": 186.40, "payerId": alex_id, "splitType": "PERCENT", "currency": "USD", "note": "Trader Joe's Shared Pantry", "categoryId": groc_cat,
            "shares": [{"userId": alex_id, "percent": 30.0}, {"userId": alice_id, "percent": 30.0}, {"userId": bob_id, "percent": 20.0}, {"userId": carol_id, "percent": 20.0}]
        }),
        (gid1, {
            "amount": 420.00, "payerId": carol_id, "splitType": "CUSTOM", "currency": "USD", "note": "Living Room 55-inch Smart TV", "categoryId": ent_cat,
            "shares": [{"userId": alex_id, "amount": 120.00}, {"userId": alice_id, "amount": 100.00}, {"userId": bob_id, "amount": 100.00}, {"userId": carol_id, "amount": 100.00}]
        }),
        (gid1, {"amount": 52.80, "payerId": alex_id, "splitType": "EQUAL", "currency": "USD", "note": "Eco Household Cleaning Pack", "categoryId": shop_cat}),

        # Group 2: Lake Tahoe Ski Trip
        (gid2, {"amount": 1250.00, "payerId": alex_id, "splitType": "EQUAL", "currency": "USD", "note": "Mountain Chalet Airbnb 3 Nights", "categoryId": trav_cat}),
        (gid2, {"amount": 640.00, "payerId": david_id, "splitType": "EQUAL", "currency": "USD", "note": "Palisades Tahoe 2-Day Lift Passes", "categoryId": ent_cat}),
        (gid2, {"amount": 320.00, "payerId": bob_id, "splitType": "EQUAL", "currency": "USD", "note": "AWD SUV Rental & Snow Chains", "categoryId": trav_cat}),
        (gid2, {"amount": 95.60, "payerId": alex_id, "splitType": "EQUAL", "currency": "USD", "note": "Highway Fuel & Bay Bridge Tolls", "categoryId": trav_cat}),
        (gid2, {
            "amount": 245.00, "payerId": alice_id, "splitType": "PERCENT", "currency": "USD", "note": "Fireside Dinner at The Ridge", "categoryId": din_cat,
            "shares": [{"userId": alex_id, "percent": 35.0}, {"userId": alice_id, "percent": 25.0}, {"userId": bob_id, "percent": 20.0}, {"userId": david_id, "percent": 20.0}]
        }),
        (gid2, {
            "amount": 110.00, "payerId": david_id, "splitType": "CUSTOM", "currency": "USD", "note": "Apres-Ski Craft Beer & Wings", "categoryId": din_cat,
            "shares": [{"userId": alex_id, "amount": 30.00}, {"userId": alice_id, "amount": 30.00}, {"userId": bob_id, "amount": 25.00}, {"userId": david_id, "amount": 25.00}]
        }),

        # Group 3: Weekend Foodies Club
        (gid3, {"amount": 380.00, "payerId": alex_id, "splitType": "EQUAL", "currency": "USD", "note": "Chef's Omakase Sushi Tasting", "categoryId": din_cat}),
        (gid3, {"amount": 48.50, "payerId": bob_id, "splitType": "EQUAL", "currency": "USD", "note": "Single-Origin Pour Over & Croissants", "categoryId": din_cat}),
        (gid3, {
            "amount": 195.00, "payerId": carol_id, "splitType": "PERCENT", "currency": "USD", "note": "Handmade Pasta & Barolo Wine", "categoryId": din_cat,
            "shares": [{"userId": alex_id, "percent": 25.0}, {"userId": bob_id, "percent": 30.0}, {"userId": carol_id, "percent": 25.0}, {"userId": david_id, "percent": 20.0}]
        }),
        (gid3, {
            "amount": 65.00, "payerId": alex_id, "splitType": "CUSTOM", "currency": "USD", "note": "French Macarons & Eclairs Box", "categoryId": din_cat,
            "shares": [{"userId": alex_id, "amount": 20.00}, {"userId": bob_id, "amount": 15.00}, {"userId": carol_id, "amount": 15.00}, {"userId": david_id, "amount": 15.00}]
        }),
        (gid3, {"amount": 78.20, "payerId": david_id, "splitType": "EQUAL", "currency": "USD", "note": "Ferry Plaza Organic Farmers Market", "categoryId": groc_cat}),
        (gid3, {"amount": 36.00, "payerId": bob_id, "splitType": "EQUAL", "currency": "USD", "note": "Artisanal Pistachio & Fig Gelato", "categoryId": din_cat}),
    ]

    created_expense_ids = []
    for gid, exp in expense_payloads:
        # Creator is Alex (except when payer creates it)
        creator_token = user_tokens["demo.reviewer@splitwise.ai"]
        code, eres = api(f"/groups/{gid}/expenses", method="POST", data=exp, token=creator_token)
        if code == 200:
            created_expense_ids.append(eres["id"])
            print(f"Created expense '{exp['note']}': ${exp['amount']} (ID: {eres['id']})")
        else:
            print(f"Failed to create expense '{exp['note']}': {code} -> {eres}")

    # 5. Settlements
    settlements = [
        (gid1, user_tokens["alice.chen@splitwise.ai"], {"fromUserId": alice_id, "toUserId": alex_id, "amount": 200.00, "currency": "USD", "note": "Partial Rent & Utilities repayment"}),
        (gid2, user_tokens["demo.reviewer@splitwise.ai"], {"fromUserId": alex_id, "toUserId": david_id, "amount": 80.00, "currency": "USD", "note": "Tahoe ski passes settlement"}),
        (gid3, user_tokens["carol.taylor@splitwise.ai"], {"fromUserId": carol_id, "toUserId": alex_id, "amount": 45.00, "currency": "USD", "note": "Sushi dinner share"})
    ]

    for gid, tok, sdata in settlements:
        code, sres = api(f"/groups/{gid}/settlements", method="POST", data=sdata, token=tok)
        print(f"Recorded settlement in group {gid} (${sdata['amount']}): {code}")

    # 6. Upload a receipt for Group 1 so Receipt Scanner page has extracted data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    try:
        with open("sample_receipt.png", "rb") as f:
            img_bytes = f.read()

        part_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="sample_receipt.png"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode("latin-1")
        part_footer = f"\r\n--{boundary}--\r\n".encode("latin-1")
        body = part_header + img_bytes + part_footer

        upload_headers = {"Authorization": f"Bearer {alex_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
        req_up = urllib.request.Request(f"{BASE_URL}/groups/{gid1}/receipts", data=body, headers=upload_headers, method="POST")
        with urllib.request.urlopen(req_up, timeout=30) as resp:
            rec_res = json.loads(resp.read().decode("utf-8"))
            rec_id = rec_res["id"]
            print(f"Uploaded demo receipt ID {rec_id} to Group {gid1}")

        # Extract it
        code_ext, ext_res = api(f"/groups/{gid1}/receipts/{rec_id}/extract", method="POST", token=alex_token)
        print(f"Extracted demo receipt {rec_id}: {code_ext} -> Merchant: {ext_res.get('merchantName')}, Subtotal: {ext_res.get('subtotal')}, Total: {ext_res.get('totalAmount')}")
    except Exception as e:
        print(f"Receipt upload error: {e}")

    # 7. Spread Dates in MySQL across multiple months (Sept, Oct, Nov 2026) for rich charts
    # Distribute the 18 expenses: 6 in Sept, 6 in Oct, 6 in Nov
    if len(created_expense_ids) >= 18:
        dates_sql = []
        for i, eid in enumerate(created_expense_ids):
            if i < 6:
                # September 2026
                d_str = f"2026-09-{10 + i * 3:02d} 14:30:00"
            elif i < 12:
                # October 2026
                d_str = f"2026-10-{5 + (i - 6) * 4:02d} 18:45:00"
            else:
                # November 2026
                d_str = f"2026-11-{2 + (i - 12) * 3:02d} 12:15:00"
            dates_sql.append(f"UPDATE expenses SET created_at = '{d_str}' WHERE id = {eid};")

        sql_cmd = " ".join(dates_sql)
        cmd = ["mysql", "-u", "root", "-pAs@32004", "-e", f"USE expense_db; {sql_cmd}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Updated expense timestamps across Sept, Oct, Nov 2026. MySQL returncode: {res.returncode}")

    print("=== DEMO DATA GENERATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
