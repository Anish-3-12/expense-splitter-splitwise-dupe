# Splitwise AI — Financial Integrity & Calculation Engine Specification

This document provides a formal mathematical and architectural specification of the financial engine in Splitwise AI.

---

## 1. Core Financial Invariants

The financial engine guarantees four fundamental invariants across all operations, database transactions, and user interactions.

```
+-----------------------------------------------------------------------------------+
|                              FINANCIAL INVARIANTS                                 |
+-----------------------------------------------------------------------------------+
|  1. Expense Share Conservation:                                                   |
|     sum(expense_shares) == total_expense_amount                                    |
|                                                                                   |
|  2. Zero-Sum Group Balances:                                                      |
|     sum(user_net_balances) == 0.00  (for every group at all times)                |
|                                                                                   |
|  3. Receipt Line-Item Integrity:                                                  |
|     sum(receipt_line_totals) == receipt_subtotal                                  |
|                                                                                   |
|  4. Receipt Final Total Reconciled Identity:                                      |
|     receipt_subtotal + tax + fees - discounts == receipt_total_amount             |
+-----------------------------------------------------------------------------------+
```

### Invariant 1: Expense Share Conservation
For any expense $E$ with total monetary amount $A$ and set of participant shares $S = \{s_1, s_2, \dots, s_n\}$:
$$\sum_{i=1}^{n} s_i = A$$
This condition is verified in `ExpenseService.java` prior to persisting any record. If the sum deviates by more than ₹0.00 (evaluated in integer minor units / paise), the transaction aborts with `HTTP 400 Bad Request`.

### Invariant 2: Group Balance Zero-Sum Conservation
For any group $G$ with members $M = \{u_1, u_2, \dots, u_m\}$, let $B(u)$ denote the net balance of user $u$:
$$B(u) = \sum \text{PaidBy}(u) - \sum \text{OwedBy}(u) + \sum \text{SettlementsReceived}(u) - \sum \text{SettlementsPaid}(u)$$
Across all members of group $G$:
$$\sum_{u \in M} B(u) = 0.00$$
Every rupee paid by one member is owed by one or more other members. Settlements directly transfer balance between two members, changing individual balances by $+S$ and $-S$ respectively, leaving $\sum B(u) = 0.00$ intact.

### Invariant 3: Receipt Line-Item Integrity
When a physical or digital receipt is scanned:
$$\sum_{k=1}^{K} \text{item}_k.\text{line\_total} = \text{receipt}.\text{subtotal}$$
Where $\text{item}_k.\text{line\_total} = \text{item}_k.\text{quantity} \times \text{item}_k.\text{unit\_price}$.
Discrepancies between OCR line items and the printed subtotal are detected and flagged as `DISCREPANCY_DETECTED`.

### Invariant 4: Receipt Tax & Total Reconciliation
The relationship between subtotal, statutory taxes, additional service charges, and discounts must satisfy:
$$\text{subtotal} + \text{tax} + \text{service\_charges} - \text{discounts} = \text{total\_amount}$$
A receipt is marked `RECONCILED` only when Invariant 3 and Invariant 4 are both satisfied with zero ambiguous item allocations.

---

## 2. Minor-Unit (Paise) Arithmetic & Rounding Guarantees

Floating-point representations (`double`, `float` in IEEE 754) introduce binary rounding artifacts (e.g. `0.1 + 0.2 = 0.30000000000000004`). In Splitwise AI:
- The database stores exact fixed-point amounts using `DECIMAL(10, 2)`.
- The Spring Boot backend executes all calculations using Java `BigDecimal` or exact integer minor units (`long paise = amount * 100`).
- The Python AI microservice models monetary amounts with `pydantic.condecimal` and Python's `decimal.Decimal`.

### Equal Split Rounding Algorithm
When dividing an amount $A$ in paise across $N$ participants:
$$\text{base\_share} = \lfloor \frac{A}{N} \rfloor$$
$$\text{remainder} = A \pmod N$$
The remainder $r$ (where $0 \le r < N$) represents indivisible paise. The algorithm allocates $(\text{base\_share} + 1)$ paise to the first $r$ participants and $\text{base\_share}$ paise to the remaining $N - r$ participants:

```java
long totalPaise = amount.multiply(BigDecimal.valueOf(100)).setScale(0, RoundingMode.HALF_UP).longValue();
long basePaise = totalPaise / memberCount;
long remainderPaise = totalPaise % memberCount;

for (int i = 0; i < memberCount; i++) {
    long sharePaise = basePaise + (i < remainderPaise ? 1 : 0);
    shares.add(BigDecimal.valueOf(sharePaise, 2));
}
```
**Example**: Dividing ₹100.00 across 3 members:
- `totalPaise` = 10000
- `basePaise` = 3333 (₹33.33)
- `remainderPaise` = 1
- Member 1: ₹33.34
- Member 2: ₹33.33
- Member 3: ₹33.33
- Total = ₹33.34 + ₹33.33 + ₹33.33 = ₹100.00 (Exact conservation).

---

## 3. Splitting Strategies

### Equal Split
- Available for general expenses and receipts.
- Divides expense equally across selected participants using the paise remainder allocation algorithm.

### Percentage Split
- Each participant is assigned an explicit percentage $p_i$.
- Engine validates: $\sum_{i=1}^{n} p_i = 100.00\%$.
- Calculated shares: $s_i = \text{round}(A \times \frac{p_i}{100})$.
- Any penny delta caused by independent rounding is absorbed into the largest share.

### Custom / Exact Split
- Each participant is assigned an explicit monetary share $s_i$.
- Engine validates: $\sum_{i=1}^{n} s_i == A$.
- If the sum deviates by even ₹0.01, validation rejects the payload with an error explaining the discrepancy amount.

### Line-Item Allocation Split
- Receipts with itemized breakdowns allow each item $k$ to be assigned to a subset of participants $P_k \subseteq M$.
- Item $k$'s amount is split equally among $P_k$.
- Total user share is the sum of their allocated item fractions plus their proportional share of taxes and service fees.

---

## 4. Multi-Currency Lifecycle & Ledger Safety Boundary

### The Single-Currency Ledger Architecture
Splitwise AI's persistent financial ledger is strictly single-currency: **INR (₹)**.
The database stores scalar values in `amount` columns without an FX rate engine.
Summing amounts of different currencies would corrupt financial balances (e.g. treating $28.11 as ₹28.11).

```
                      +----------------------------------------+
                      |       Physical / Digital Receipt       |
                      |   (USD $28.11, EUR €50.00, INR ₹1200)  |
                      +----------------------------------------+
                                          |
                                    OCR & Vision
                                          v
                      +----------------------------------------+
                      |       Receipt Extraction (Python)      |
                      |  - Detected Currency preserved (USD)   |
                      |  - Amounts preserved ($25.97, $28.11)  |
                      |  - Validation against receipt math     |
                      +----------------------------------------+
                                          |
                               Spring Boot Review API
                                          v
                      +----------------------------------------+
                      |         Receipt Entity Stored          |
                      |   currency="USD", total=28.11          |
                      |   status=EXTRACTED / REVIEWED          |
                      |   Original currency is IMMUTABLE       |
                      +----------------------------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
            Receipt Currency == "INR"                 Receipt Currency != "INR"
                     |                                         |
                     v                                         v
         +-----------------------+                 +-----------------------+
         |     Confirm Receipt   |                 |    POST /confirm      |
         |        (HTTP 200)     |                 |      REJECTED         |
         | Creates Expense in    |                 |   (HTTP 422 Error)    |
         | INR Financial Ledger  |                 | "Foreign Currency     |
         +-----------------------+                 |  Ledger Restriction"  |
                                                   +-----------------------+
```

### Safety Guarantees:
1. **Document Fidelity**: Foreign currency receipts preserve their true currency code (`USD`, `EUR`, `GBP`) and monetary values during OCR extraction, database persistence, and review.
2. **Posting Restriction**: Calling `POST /api/groups/{groupId}/receipts/{id}/confirm` on a non-INR receipt returns `HTTP 422 Unprocessable Entity` and creates zero expense records.
3. **Immutability of Detected Currency**: Users cannot tamper with or override a receipt's detected currency during review to bypass ledger checks (`HTTP 400 Bad Request`).
4. **Direct API Protection**: `POST /api/groups/{groupId}/expenses` and `POST /api/groups/{groupId}/settlements` reject payloads with `currency != "INR"` with `HTTP 400 Bad Request`.
5. **Natural Language Guard**: Prompts with foreign currency markers (`$50`, `100 EUR`, `dollars`) return `clarification_required = True` and refuse to populate INR amount drafts.
6. **Frontend UI Disclosure**: The UI displays an explicit warning alert and disables the confirmation button with `"Posting Restricted (USD Ledger Mismatch)"`.

---

## 5. Settlement & Debt Simplification

### Balance Model
Each member's net position is maintained as a signed decimal:
- Positive balance ($> 0$): Member is a net **creditor** (owed money by the group).
- Negative balance ($< 0$): Member is a net **debtor** (owes money to the group).
- Zero balance ($= 0$): Member is settled up.

### Settlement Validation
When recording a settlement from User $A$ (debtor) to User $B$ (creditor) for amount $S$:
1. $A$ and $B$ must both be active members of the group (`HTTP 400`).
2. Amount $S$ must be positive ($S > 0$) and in INR.
3. Once recorded, the balance updates immediately:
   $$B'(A) = B(A) + S$$
   $$B'(B) = B(B) - S$$
   Since $B(A) < 0$, adding $S$ brings $A$ closer to 0. Since $B(B) > 0$, subtracting $S$ brings $B$ closer to 0.

### Idempotency & Concurrency Safety
- All expense and settlement additions execute inside database transactions with `@Transactional`.
- Receipt confirmation employs pessimistic row locking (`findByIdAndGroupIdForUpdate`) to guarantee that concurrent confirmation requests result in exactly one successful confirmation (`HTTP 200`) and subsequent requests receive `HTTP 409 Conflict`.
