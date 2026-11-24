import urllib.request
import json

def req(url, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode())

def post(url, data):
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(data).encode()
    r = urllib.request.Request(url, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode())

def main():
    login = post('http://localhost:8080/api/auth/login', {'email': 'demo.reviewer@splitwise.ai', 'password': 'Password123!'})
    token = login['token']
    me = req('http://localhost:8080/api/auth/me', token)
    print('Login success! User:', me['name'])

    groups = req('http://localhost:8080/api/groups', token)
    print('\n=== GROUPS LIST ===')
    for g in groups:
        print(f"ID: {g['id']} | Name: {g['name']} | MemberCount: {g.get('memberCount')}")

    gid = groups[0]['id']
    print(f'\n=== GROUP {gid} EXPENSES ===')
    expenses = req(f'http://localhost:8080/api/groups/{gid}/expenses', token)
    for e in expenses:
        print(f"Exp #{e['id']} | Note: {e.get('note')} | Amount: ₹{e.get('amount')} | Payer: {e.get('payerName')} (ID: {e.get('payerId')}) | Category: {e.get('categoryName')}")

    print(f'\n=== GROUP {gid} ANALYTICS ===')
    analytics = req(f'http://localhost:8080/api/groups/{gid}/analytics/overview', token)
    print(f"Total Expenditure: {analytics.get('totalExpenditure')}")
    print(f"Total Spending: {analytics.get('totalSpending')}")
    print(f"Average Expense: {analytics.get('averageExpense')}")
    print(f"Expense Count: {analytics.get('expenseCount')}")

    print('\nMember Spending Breakdown:')
    for m in analytics.get('memberSpending', []):
        print(f"  {m['userName']}: Paid ₹{m['totalPaid']} | Share ₹{m['totalShare']} | Net ₹{m['netBalance']} | Pct: {m.get('percentage')}%")

    print('\nAnomalies:')
    for a in analytics.get('anomalies', []):
        print(f"  Expense #{a['expenseId']} | Note: {a.get('expenseNote')} | Amount: ₹{a['amount']} | Payer: {a.get('payerName')} | Category: {a.get('categoryName')} | Status: {a.get('status')} | Reason: {a.get('reason')}")

    print('\nMonthly Spending:')
    for m in analytics.get('monthlySpending', []):
        print(f"  Month: {m['month']} | Amount: ₹{m['amount']} | Count: {m['count']}")

if __name__ == '__main__':
    main()
