# Splitwise AI — Portfolio Guide, Resume Impact & Deep Technical Interview Q&A

This document prepares software engineers to present Splitwise AI in high-stakes technical interviews, resume profiles, and portfolio presentations.

---

## 1. Resume Project Bullets (STAR Format)

### Full-Stack / Backend Engineer Bullet Options:
- **Architected and delivered Splitwise AI**, a production-grade microservices expense-sharing platform using **Spring Boot 3 (Java 21)**, **Python FastAPI**, **MySQL 8.0**, and **React 19**, processing complex group debts with zero-sum mathematical guarantees.
- **Engineered an autonomous AI receipt reconciliation pipeline** combining **OpenCV**, **Tesseract OCR**, and local **Ollama LLMs (Qwen 2.5 1.5B)** to extract line items and enforce integer minor-unit financial invariants (`sum(items) == subtotal` and `subtotal + tax == total`), eliminating manual itemization.
- **Implemented rigorous financial safety boundaries**, restricting multi-currency receipt contamination through Spring Boot validation, preventing floating-point rounding errors via integer-paise arithmetic, and guaranteeing confirmation idempotency using database row-level locking (`SELECT FOR UPDATE`).
- **Designed dual-tier unsupervised anomaly detection** utilizing statistical **Interquartile Range (IQR)** and **Scikit-Learn Isolation Forest** to dynamically flag unusual transactions as actionable review suggestions.
- **Authored comprehensive regression test suites** across Java MockMvc and Python Pytest (**73 passing automated tests**), covering concurrent execution, group authorization boundaries, receipt math verification, and currency injection guards.

---

## 2. 60-Second Elevator Pitch

> *"Splitwise AI is a full-stack, AI-augmented expense management system built with Spring Boot, Python FastAPI, MySQL, and React. While traditional expense splitters rely on tedious manual entry, Splitwise AI introduces two major autonomous capabilities: natural-language split interpretation and receipt vision reconciliation using local, open-source LLMs and OCR.
>
> Crucially, rather than treating AI output as blindly trusted truth, I architected the platform with a strict deterministic financial boundary: Spring Boot serves as the ultimate authority, enforcing integer minor-unit arithmetic, row-level pessimistic concurrency locking, and zero-sum balance conservation. Even if the AI hallucinates, the system guarantees that all shares sum exactly to the penny and no foreign currency corrupts the ledger."*

---

## 3. Deep Technical Interview Q&A (15 Core Questions)

### Q1: Why did you split the architecture into a Spring Boot backend and a Python FastAPI service instead of doing everything in one language?
**Answer**:
*"I designed this around domain boundaries and ecosystem strengths.
Financial ledgers demand strict transactional integrity, compile-time type safety, robust relational ORM tooling, and enterprise security frameworks—areas where Java and Spring Boot 3 excel.
Conversely, computer vision, OCR, and open-source machine learning ecosystems are vastly superior and more idiomatic in Python (OpenCV, PyTesseract, Scikit-Learn, Pydantic).
Separating them into a Spring Boot financial core and a Python AI microservice keeps the financial ledger isolated from resource-intensive machine learning workloads, enables independent scaling, and secures inter-service communication via pre-shared secrets (`X-Internal-Secret`)."*

---

### Q2: How do you prevent floating-point rounding errors in financial calculations?
**Answer**:
*"In financial systems, binary floating-point types (`float` and `double` in IEEE 754) produce catastrophic rounding artifacts because numbers like 0.1 cannot be represented exactly in binary.
In Splitwise AI:
1. In the database, all monetary values are stored as fixed-point `DECIMAL(10, 2)`.
2. In Java, all splitting calculations use exact integer minor units (paise) represented as `long` or `BigDecimal` with explicit rounding modes (`RoundingMode.HALF_UP`).
3. For equal splits where an amount cannot be evenly divided (e.g. dividing ₹100.00 among 3 people), our algorithm calculates the quotient `10000 / 3 = 3333` paise and remainder `10000 % 3 = 1` paisa. The remainder penny is distributed to the first participant so that $\sum \text{shares} = 33.34 + 33.33 + 33.33 = 100.00$, preserving the invariant down to the exact single paisa."*

---

### Q3: Explain the multi-currency architecture. Why is foreign currency posting restricted?
**Answer**:
*"The database financial ledger operates strictly in single currency (INR). Columns store scalar numbers without a live dynamic currency exchange rate engine. If a user scanned a USD receipt for $28.11 and the system allowed it to post directly, the ledger would record it as ₹28.11, corrupting group balances and undercounting the payer's credit by an order of magnitude.
Instead, we implemented a document-fidelity boundary:
- The OCR and AI extraction pipeline faithfully preserves original detected currencies (`USD`, `EUR`, `GBP`) and printed monetary amounts.
- In the review interface, foreign receipts are marked with an explicit restriction banner and the confirmation button is disabled.
- If a client bypasses the UI and attempts to call `POST /api/groups/{id}/receipts/{id}/confirm` on a non-INR receipt, Spring Boot returns `HTTP 422 Unprocessable Entity` and creates zero expense records.
- In natural language splitting, if a prompt mentions '$50' or 'EUR', the AI microservice returns `clarification_required = True` rather than silently converting it."*

---

### Q4: How do you handle race conditions when two users attempt to confirm the same receipt simultaneously?
**Answer**:
*"Receipt confirmation triggers expense creation, expense shares insertion, and ledger balance adjustments. If two roommates click 'Confirm' simultaneously or a network retry duplicates a POST request, a naive system would create duplicate expenses.
We solve this using two layers of protection:
1. **Pessimistic Row-Level Locking**: In `ReceiptService.java`, the confirmation query executes `findByIdAndGroupIdForUpdate(receiptId, groupId)`, issuing a `SELECT ... FOR UPDATE` in MySQL InnoDB. The second transaction is blocked until the first transaction commits.
2. **State Transition Check & Idempotency**: Once Thread 1 completes, it marks the receipt `status = CONFIRMED` and commits. When Thread 2 acquires the lock, it immediately checks `if (receipt.getStatus() == Receipt.Status.CONFIRMED)` and throws `HTTP 409 Conflict`.
We verified this behavior with a 4-thread concurrent integration test (`testConcurrentReceiptConfirmation`), proving that exactly 1 request succeeds (200 OK) and 3 fail with 409 Conflict."*

---

### Q5: How do you prevent local LLMs from hallucinating fabricated user IDs during natural language splitting?
**Answer**:
*"Hallucination is a major risk when asking an LLM to assign financial liabilities. An LLM might invent a user ID like `999` or attribute money to an unauthorized person.
We eliminate this through **context grounding and schema constraint**:
1. When the user requests an AI split, Spring Boot queries the database for active group members and passes the exact list `[{"id": 12, "name": "Alex"}, {"id": 13, "name": "Alice"}]` to FastAPI.
2. The system prompt injects these members into an explicit few-shot template and instructs the model: *'CRITICAL: Only use member IDs from the authorized roster above. Never invent IDs.'*
3. After the LLM outputs JSON, our Python validation layer parses it with Pydantic and enforces `assert pid in valid_member_ids`. Any ID not in the roster is stripped or triggers a clarification request."*

---

### Q6: How does the receipt OCR pipeline distinguish subtotal, tax, and final total?
**Answer**:
*"Receipts have varied layouts. We implemented a two-stage invariant verification engine:
- **Invariant 1**: $\sum \text{line\_items} == \text{subtotal}$.
- **Invariant 2**: $\text{subtotal} + \text{tax} == \text{final\_total}$.
If an LLM or OCR engine accidentally sets the subtotal equal to the final total (e.g. reporting subtotal = $28.11, tax = $2.14, total = $28.11), our validation engine flags this as mathematically impossible: $28.11 + 2.14 \ne 28.11$.
In such cases, the system recalculates the line-item sum ($25.97), verifies that $25.97 + 2.14 == 28.11$, and flags any irreconcilable ambiguity with status `DISCREPANCY_DETECTED`. The raw OCR text is preserved so the user can verify the original printed document."*

---

### Q7: Why did you implement dual anomaly detection algorithms (IQR vs Isolation Forest)?
**Answer**:
*"Machine learning algorithms have minimum sample size requirements.
An unsupervised algorithm like Isolation Forest struggles on small datasets (e.g. 5 or 6 expenses) because high-dimensional decision trees overfit and produce erratic outlier scores.
To solve this gracefully:
- For groups with **5 to 19 expenses**, we execute a non-parametric **Statistical Interquartile Range (IQR)** baseline. The upper threshold is defined as $Q_3 + 1.5 \times \text{IQR}$.
- Once a group reaches **20 or more expenses**, the service automatically transitions to **Scikit-Learn Isolation Forest**, which evaluates both normalized transaction amount and one-hot encoded category vectors.
- The API explicitly returns the algorithm used (`anomalyDetectionAlgorithm`), and all anomalies are framed as constructive review suggestions (`REQUIRES_REVIEW`) rather than accusations of fraud."*

---

### Q8: How is multi-tenant security enforced across groups?
**Answer**:
*"Multi-tenancy is enforced at both the HTTP security filter layer and the service layer.
Every incoming request validates the JWT in `JwtAuthenticationFilter`, setting the authenticated `User` principal.
Whenever an operation targets a group route `/api/groups/{groupId}/*`:
1. `validateGroupMembership(group, user)` queries the `group_members` join table.
2. If the authenticated user is not an active member, the request immediately terminates with `HTTP 403 Forbidden`.
3. Non-members cannot view group metadata, view expenses, upload receipts, or review financial balances."*

---

### Q9: Why did you choose Material UI v7 Grid with the `size` property over legacy `xs`/`md`?
**Answer**:
*"In Material UI v7, the Grid component was updated to align with the CSS Grid specification. The legacy `<Grid item xs={12} md={6}>` syntax was deprecated in favor of `<Grid size={{ xs: 12, md: 6 }}>`.
Using deprecated props in MUI v7 causes layout bugs where cards collapse to minimal intrinsic widths on mobile screens or fail to render side-by-side on desktop.
We modernized every Grid instance across Dashboard, Settlements, AddExpense, and ReceiptScanner, ensuring 100% full-width cards on mobile and an optimal 5/12 + 7/12 layout on desktop."*

---

### Q10: How do you verify the zero-sum invariant across group balances?
**Answer**:
*"In group balance mathematics, money cannot be created or destroyed.
For every expense paid by user $A$ and shared with user $B$, $A$'s balance increases by $+S$ and $B$'s balance decreases by $-S$.
The sum of all member net balances must always equal 0.00:
$$\sum_{u \in M} \text{netBalance}(u) == 0.00$$
Our automated tests (`SplitwiseAiIntegrationTest.testSettlementRecordingAndBalanceInvariant`) compute `sum += balance.getNetBalance()` and assert `assertThat(Math.abs(sum)).isLessThan(0.01)` after both expenses and settlements."*

---

### Q11: What status codes do your APIs return, and why do you distinguish 400, 409, and 422?
**Answer**:
*"Using precise HTTP semantics is critical for API clarity:
- **400 Bad Request**: Used for malformed payloads, invalid split percentages, or direct requests specifying non-INR currency.
- **404 Not Found**: Used when requested group, receipt, or expense IDs do not exist in the database.
- **409 Conflict**: Used specifically for concurrency and idempotency violations, such as attempting to confirm an already confirmed receipt.
- **422 Unprocessable Entity**: Used when a request is syntactically valid JSON, but violates an invariant business rule—specifically, attempting to confirm a foreign-currency receipt (e.g. USD) into the INR-only financial ledger."*

---

### Q12: How long does Ollama inference take on CPU, and how does your architecture prevent HTTP timeouts?
**Answer**:
*"On a standard developer laptop running a 1.5B quantized model on CPU, natural language parsing takes ~20–30s and multi-item receipt extraction takes ~35–45s.
To prevent premature connection drops:
1. `RestTemplateBuilder` in Spring Boot sets `readTimeout` and `connectTimeout` to 120 seconds (`app.ai-service.timeout-ms: 120000`).
2. FastAPI's inference timeout is configured to 90 seconds.
3. The frontend React client displays animated loading progress indicators ('Thinking...' and 'Extracting...') while keeping the user informed."*

---

### Q13: What happens if Tesseract OCR fails to recognize text on a blurred receipt?
**Answer**:
*"The receipt service implements a resilient fallback hierarchy:
1. OpenCV preprocessing sharpens and normalizes contrast.
2. If OCR extracts empty text, the AI service returns a safe default schema with `subtotal: null`, `total: null`, and `validation_status: UNKNOWN`.
3. The frontend opens the review modal with blank fields, enabling the user to manually enter the merchant, date, and line items.
4. The system never crashes or corrupts existing records when vision extraction fails."*

---

### Q14: What is your automated test coverage?
**Answer**:
*"Splitwise AI has **73 passing automated tests**:
- **35 Spring Boot Tests**: Covering user authentication, multi-tenant group permissions, concurrent receipt confirmation, minor-unit rounding math, foreign currency rejection (400 and 422), and balance invariants.
- **38 Python Pytest Tests**: Covering OpenCV preprocessing, Tesseract extraction, regex fallback parsing, currency detection, prompt foreign-currency interception, and Scikit-Learn Isolation Forest anomaly detection.
- **Frontend Production Build**: Vite compiles 11,700+ modules with zero errors."*

---

### Q15: What would be your technical roadmap for taking this system to a multi-million user production deployment?
**Answer**:
*"The enterprise production roadmap includes:
1. **Dynamic FX Rate Engine**: Integrate a real-time FX service (e.g. Open Exchange Rates) to allow multi-currency ledgers with historical conversion snapshots.
2. **Asynchronous OCR Job Queue**: Offload receipt OCR to asynchronous workers via RabbitMQ / Apache Kafka with WebSocket notifications to the client.
3. **GPU-Accelerated Inference Cluster**: Deploy Ollama or vLLM on Kubernetes nodes with NVIDIA GPUs, reducing inference latency from 30s to <1.5s.
4. **Redis Balance Caching**: Cache group balance matrices in Redis with transactional cache invalidation on new expense/settlement events."*
