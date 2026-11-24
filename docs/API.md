# Splitwise AI — REST API Reference & Status Code Specification

This document provides complete documentation for the Splitwise AI REST endpoints, including authentication schemes, request/response JSON schemas, error handling, and status code behavior.

---

## 1. Authentication & Protocols

- **Base URL (Spring Boot Backend)**: `http://localhost:8080/api`
- **Base URL (Internal AI Service)**: `http://localhost:8000/internal/v1`
- **User Authentication**: Client requests to protected backend routes must include:
  ```http
  Authorization: Bearer <jwt_token>
  ```
- **Service-to-Service Security**: Spring Boot requests to FastAPI must include:
  ```http
  X-Internal-Secret: <INTERNAL_API_SECRET>
  ```

---

## 2. HTTP Status Code Conventions

| Status Code | Meaning | Example Trigger |
|:-----------:|:--------|:----------------|
| **200 OK** | Request succeeded | Successful query or update. |
| **201 Created** | Entity created | Successful registration or expense creation. |
| **400 Bad Request** | Validation failed | Unequal share sum; currency tampering in review; foreign currency direct expense. |
| **401 Unauthorized** | Missing/Invalid credentials | Expired JWT or missing Bearer token. |
| **403 Forbidden** | Authorization boundary | Non-member user attempts to read or mutate another group. |
| **404 Not Found** | Resource missing | Group, expense, or receipt ID does not exist. |
| **409 Conflict** | Idempotency / Concurrency violation | Calling `POST /confirm` on an already confirmed receipt. |
| **422 Unprocessable Entity** | Business rule invariant rejection | Attempting to confirm a foreign currency receipt (e.g. USD) into the INR-only ledger. |

---

## 3. Authentication Endpoints

### Register User
`POST /api/auth/register`

**Request:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "Password123!"
}
```

**Response (200 OK):**
```json
{
  "id": 16,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### User Login
`POST /api/auth/login`

**Request:**
```json
{
  "email": "demo.reviewer@splitwise.ai",
  "password": "Password123!"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "type": "Bearer",
  "id": 12,
  "email": "demo.reviewer@splitwise.ai",
  "name": "Alex Morgan"
}
```

---

## 4. Group Management

### List User Groups
`GET /api/groups` (Headers: `Authorization: Bearer <token>`)

**Response (200 OK):**
```json
[
  {
    "id": 13,
    "name": "Apartment 4B Roommates",
    "description": "Shared household bills",
    "memberCount": 4,
    "createdAt": "2026-11-20T10:00:00Z"
  }
]
```

### Get Group Details & Members
`GET /api/groups/{groupId}`

**Response (200 OK):**
```json
{
  "id": 13,
  "name": "Apartment 4B Roommates",
  "description": "Shared household bills",
  "members": [
    {"userId": 12, "name": "Alex Morgan", "email": "demo.reviewer@splitwise.ai", "role": "ADMIN"},
    {"userId": 13, "name": "Alice Chen", "email": "alice.chen@example.com", "role": "MEMBER"},
    {"userId": 14, "name": "Bob Martinez", "email": "bob.martinez@example.com", "role": "MEMBER"},
    {"userId": 15, "name": "Carol Taylor", "email": "carol.taylor@example.com", "role": "MEMBER"}
  ]
}
```

---

## 5. Expenses & Financial Calculations

### Create Manual Expense
`POST /api/groups/{groupId}/expenses`

**Request (Equal Split):**
```json
{
  "amount": 1200.00,
  "currency": "INR",
  "payerId": 12,
  "splitType": "EQUAL",
  "categoryId": 1,
  "note": "Dinner at Toit",
  "participantIds": [12, 13, 14, 15]
}
```

**Response (200 OK):**
```json
{
  "id": 26,
  "groupId": 13,
  "payerId": 12,
  "payerName": "Alex Morgan",
  "amount": 1200.00,
  "currency": "INR",
  "splitType": "EQUAL",
  "categoryName": "Dining & Drinks",
  "note": "Dinner at Toit",
  "shares": [
    {"userId": 12, "userName": "Alex Morgan", "shareAmount": 300.00},
    {"userId": 13, "userName": "Alice Chen", "shareAmount": 300.00},
    {"userId": 14, "userName": "Bob Martinez", "shareAmount": 300.00},
    {"userId": 15, "userName": "Carol Taylor", "shareAmount": 300.00}
  ]
}
```

**Error Scenario (Non-INR Currency):**
```json
// Request with currency: "USD"
// Response Status: 400 Bad Request
{
  "status": 400,
  "error": "Bad Request",
  "message": "Invalid currency 'USD'. Only INR is supported."
}
```

### Get Group Net Balances
`GET /api/groups/{groupId}/balances`

**Response (200 OK):**
```json
[
  {"userId": 12, "userName": "Alex Morgan", "netBalance": 1593.70},
  {"userId": 13, "userName": "Alice Chen", "netBalance": -545.50},
  {"userId": 14, "userName": "Bob Martinez", "netBalance": -661.35},
  {"userId": 15, "userName": "Carol Taylor", "netBalance": -386.85}
]
// Invariant check: 1593.70 + (-545.50) + (-661.35) + (-386.85) == 0.00
```

---

## 6. Debt Settlements

### Record Settlement
`POST /api/groups/{groupId}/settlements`

**Request:**
```json
{
  "fromUserId": 13,
  "toUserId": 12,
  "amount": 545.50,
  "currency": "INR",
  "note": "Settled via Google Pay"
}
```

**Response (200 OK):**
```json
{
  "id": 8,
  "groupId": 13,
  "fromUserId": 13,
  "fromUserName": "Alice Chen",
  "toUserId": 12,
  "toUserName": "Alex Morgan",
  "amount": 545.50,
  "currency": "INR",
  "note": "Settled via Google Pay",
  "createdAt": "2026-11-24T18:00:00Z"
}
```

---

## 7. AI Expense Interpretation & Receipt Pipeline

### Natural Language Expense Split Interpretation
`POST /api/groups/{groupId}/ai/interpret-split`

**Request:**
```json
{
  "instruction": "Alex paid 1200 for dinner. Alex takes 50 percent, Alice and Bob take 25 percent each. Carol is excluded."
}
```

**Response (200 OK):**
```json
{
  "description": "Dinner",
  "totalAmount": 1200.00,
  "payerId": 12,
  "payerName": "Alex Morgan",
  "splitType": "PERCENT",
  "shares": [
    {"userId": 12, "userName": "Alex Morgan", "shareAmount": 600.00, "percentage": 50.0},
    {"userId": 13, "userName": "Alice Chen", "shareAmount": 300.00, "percentage": 25.0},
    {"userId": 14, "userName": "Bob Martinez", "shareAmount": 300.00, "percentage": 25.0}
  ],
  "clarificationRequired": false,
  "confidence": 0.95
}
```

### Upload Receipt
`POST /api/groups/{groupId}/receipts` (Multipart `file`)

**Response (200 OK):**
```json
{
  "id": 5,
  "groupId": 13,
  "status": "UPLOADED",
  "originalFilename": "sample_receipt.png",
  "fileSize": 184520,
  "currency": "INR"
}
```

### Extract Receipt OCR & Math Verification
`POST /api/groups/{groupId}/receipts/{receiptId}/extract`

**Response (200 OK):**
```json
{
  "id": 5,
  "status": "EXTRACTED",
  "merchantName": "Supermarket Grocery",
  "receiptDate": "2026-11-18",
  "currency": "USD",
  "currencySymbol": "$",
  "subtotal": 25.97,
  "tax": 2.14,
  "totalAmount": 28.11,
  "validationStatus": "RECONCILED",
  "discrepancyAmount": 0.00,
  "items": [
    {"lineNumber": 1, "description": "Organic Whole Milk", "quantity": 1.0, "unitPrice": 4.99, "lineTotal": 4.99},
    {"lineNumber": 2, "description": "Artisan Sourdough Bread", "quantity": 1.0, "unitPrice": 7.50, "lineTotal": 7.50},
    {"lineNumber": 3, "description": "Hass Avocados (Pack)", "quantity": 1.0, "unitPrice": 4.00, "lineTotal": 4.00},
    {"lineNumber": 4, "description": "Fair Trade Coffee Beans", "quantity": 1.0, "unitPrice": 8.49, "lineTotal": 8.49},
    {"lineNumber": 5, "description": "Reusable Tote Bag", "quantity": 1.0, "unitPrice": 0.99, "lineTotal": 0.99}
  ]
}
```

### Review Receipt Data
`PUT /api/groups/{groupId}/receipts/{receiptId}/review`

**Request:**
```json
{
  "merchantName": "Supermarket Grocery",
  "receiptDate": "2026-11-18",
  "currency": "USD",
  "subtotal": 25.97,
  "tax": 2.14,
  "totalAmount": 28.11,
  "items": [...]
}
```

**Error Scenario (Currency Tampering):**
```json
// Attempting to change currency from "USD" to "INR"
// Response Status: 400 Bad Request
{
  "status": 400,
  "error": "Bad Request",
  "message": "Cannot modify extracted receipt currency from 'USD' to 'INR'. Original document currency is immutable."
}
```

### Confirm Receipt (Post to Ledger)
`POST /api/groups/{groupId}/receipts/{receiptId}/confirm`

**Request:**
```json
{
  "payerId": 12,
  "splitType": "EQUAL",
  "categoryId": 2,
  "note": "Groceries from Supermarket"
}
```

**Foreign Currency Rejection (422 Unprocessable Entity):**
```json
// If receipt currency is "USD"
// Response Status: 422 Unprocessable Entity
{
  "status": 422,
  "error": "Unprocessable Entity",
  "message": "Cannot confirm receipt in foreign currency 'USD'. The expense ledger only supports INR (₹). Foreign currency receipts cannot be posted directly into the ledger."
}
```

**Idempotency Collision (409 Conflict):**
```json
// If receipt has already been confirmed
// Response Status: 409 Conflict
{
  "status": 409,
  "error": "Conflict",
  "message": "Receipt has already been confirmed with expense id: 25"
}
```

---

## 8. Group Analytics & Anomaly Detection

### Get Group Analytics
`GET /api/groups/{groupId}/analytics`

**Response (200 OK):**
```json
{
  "groupId": 13,
  "totalSpending": 3284.70,
  "averageExpense": 547.45,
  "expenseCount": 6,
  "anomalyDetectionAlgorithm": "Statistical IQR Baseline",
  "memberSpending": [
    {"userId": 12, "userName": "Alex Morgan", "totalPaid": 2639.20, "netBalance": 1593.70, "percentage": 80.35},
    {"userId": 13, "userName": "Alice Chen", "totalPaid": 80.00, "netBalance": -545.50, "percentage": 2.44},
    {"userId": 14, "userName": "Bob Martinez", "totalPaid": 145.50, "netBalance": -661.35, "percentage": 4.43},
    {"userId": 15, "userName": "Carol Taylor", "totalPaid": 420.00, "netBalance": -386.85, "percentage": 12.79}
  ],
  "anomalies": [
    {
      "expenseId": 13,
      "note": "November Apartment Rent",
      "amount": 2400.00,
      "payerName": "Alex Morgan",
      "categoryName": "Housing & Rent",
      "reviewStatus": "REQUIRES_REVIEW",
      "reason": "Significantly higher than typical group spending (IQR upper bound ₹759.44)."
    }
  ]
}
```
