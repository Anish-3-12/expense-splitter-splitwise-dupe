# REST API Reference Documentation

**Base URL**: `http://localhost:8080/api`
**Authentication**: Bearer Token (`Authorization: Bearer <jwt_token>`)
**Format**: JSON

---

## 1. Authentication APIs

### `POST /auth/register`
Create a new user account.
- **Request Body**:
  ```json
  {
    "name": "Alex Johnson",
    "email": "alex@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**: `200 OK`

### `POST /auth/login`
Authenticate and obtain a JWT token.
- **Request Body**:
  ```json
  {
    "email": "alex@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsIn...",
    "tokenType": "Bearer"
  }
  ```

### `GET /auth/me`
Retrieve authenticated user profile.
- **Response**: `200 OK`
  ```json
  {
    "id": 1,
    "name": "Alex Johnson",
    "email": "alex@example.com"
  }
  ```

---

## 2. Group Management APIs

### `GET /groups`
List all groups the authenticated user belongs to.
- **Response**: `200 OK` (Array of GroupDto)

### `POST /groups`
Create a new group.
- **Request Body**:
  ```json
  {
    "name": "Goa Trip 2026"
  }
  ```
- **Response**: `200 OK` (GroupDto with `id`, `name`, `ownerId`)

### `GET /groups/{id}`
Retrieve group details and member roster.

### `POST /groups/{id}/members`
Add a member to a group by email.
- **Request Body**:
  ```json
  {
    "email": "friend@example.com",
    "role": "MEMBER"
  }
  ```

---

## 3. Expense & Split APIs

### `GET /groups/{id}/expenses`
Retrieve all expenses for a group.

### `POST /groups/{id}/expenses`
Create a new expense with mathematical split reconciliation.
- **Request Body**:
  ```json
  {
    "amount": 1500.00,
    "payerId": 1,
    "splitType": "EQUAL",
    "currency": "INR",
    "note": "Dinner at Cafe",
    "categoryId": 2,
    "shares": [
      {"userId": 1},
      {"userId": 2},
      {"userId": 3}
    ]
  }
  ```
- **Supported `splitType`**:
  - `EQUAL`: Deterministically divides paise among provided shares or all group members.
  - `PERCENT`: Validates shares sum to exactly 100.00%.
  - `CUSTOM`: Validates shares sum to total expense amount.

### `GET /groups/{id}/balances`
Get real-time net balances for all group members. Guaranteed invariant:
$$\sum \text{netBalance} = 0.00$$

---

## 4. Settlement APIs

### `GET /groups/{id}/settlements`
Retrieve history of recorded direct peer-to-peer settlements.

### `POST /groups/{id}/settlements`
Record a peer settlement.
- **Request Body**:
  ```json
  {
    "fromUserId": 2,
    "toUserId": 1,
    "amount": 500.00,
    "currency": "INR",
    "note": "Settled via UPI"
  }
  ```

---

## 5. AI Receipt APIs

### `POST /groups/{id}/receipts`
Upload physical receipt image (`multipart/form-data`).
- **Form Data**: `file` (image binary)
- **Response**: `200 OK` (`ReceiptDto` with status `PENDING`)

### `POST /groups/{id}/receipts/{receiptId}/extract`
Trigger OpenCV & Ollama extraction.
- **Response**: `200 OK` (`ReceiptDto` with status `EXTRACTED`, `merchantName`, `totalAmount`, `items`)

### `PUT /groups/{id}/receipts/{receiptId}/review`
Review and update line items.
- **Request Body**: `ReviewReceiptRequest`

### `POST /groups/{id}/receipts/{receiptId}/confirm`
Convert verified receipt into an active group expense.
- **Request Body**: `ConfirmReceiptRequest`

---

## 6. AI Natural Language & Analytics APIs

### `POST /ai/split/interpret`
Translate natural language into structured shares via Ollama.
- **Request Body**:
  ```json
  {
    "text": "Dinner was 1800. Bob paid. Alice had 300 extra so split rest equally with Charlie.",
    "groupMembers": [{"id": 1, "name": "Bob"}, {"id": 2, "name": "Alice"}, {"id": 3, "name": "Charlie"}]
  }
  ```

### `GET /groups/{id}/analytics/overview`
Retrieve group spending analytics, monthly trajectory, category breakdown, and AI anomaly detection flags.

### `GET /users/me/dashboard`
Retrieve user-level holistic dashboard metrics across all sharing groups.
