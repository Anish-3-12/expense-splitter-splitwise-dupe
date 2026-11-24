# Splitwise AI — Architecture Specification & System Design

This document details the architectural topology, service communication boundaries, concurrency models, and end-to-end data pipelines powering Splitwise AI.

---

## 1. Executive System Overview

Splitwise AI is a hybrid microservices platform engineered for autonomous expense management, intelligent receipt reconciliation, and group debt settlement. The system combines:
1. **Deterministic Financial Core**: A Spring Boot 3 Java backend enforcing transactional consistency, multi-tenant authorization, integer-minor arithmetic, and relational integrity.
2. **Local Machine Learning Microservice**: A Python FastAPI microservice executing local OCR (Tesseract), local LLM inference (Ollama `qwen2.5:1.5b`), and anomaly detection algorithms (IQR and Scikit-Learn Isolation Forest).
3. **Single-Page Application**: A modern React 19 / Vite client utilizing Material UI v7, providing real-time visual feedback, responsive layouts, and natural language interfaces.

---

## 2. Network Topology & Ports

```
+---------------------------------------------------------------------------------+
|                                 PORT ALLOCATION                                 |
+---------------------------------------------------------------------------------+
|  Port 5173  : React Frontend (Vite Single Page Application)                     |
|  Port 8080  : Spring Boot REST API (Authentication, Ledger, Business Logic)      |
|  Port 8000  : Python FastAPI Microservice (AI Split, Receipt Vision, Analytics) |
|  Port 3306  : MySQL 8.0 Relational Database                                     |
|  Port 11434 : Ollama Local LLM Daemon (`qwen2.5:1.5b`)                          |
+---------------------------------------------------------------------------------+
```

---

## 3. Comprehensive Mermaid Diagrams

### Diagram 1: System Context Diagram (C4 Level 1)
```mermaid
graph TD
    User["End User (Mobile & Desktop Browser)"]
    SplitwiseAI["Splitwise AI System"]
    MySQL[("MySQL 8.0 Database")]
    OllamaEngine["Local Ollama Daemon (qwen2.5:1.5b)"]

    User -->|"HTTPS / REST (JWT Auth)"| SplitwiseAI
    SplitwiseAI -->|"JDBC / SQL"| MySQL
    SplitwiseAI -->|"HTTP Local IPC"| OllamaEngine
```

---

### Diagram 2: Container Diagram (C4 Level 2)
```mermaid
graph TD
    subgraph ClientLayer ["Client Tier"]
        SPA["React 19 SPA (Port 5173)\nMaterial UI v7, Axios, Context API"]
    end

    subgraph BackendTier ["Financial Backend Tier"]
        SpringBoot["Spring Boot 3.5.5 (Port 8080)\nSpring Security, JPA, Flyway, HikariCP"]
    end

    subgraph AITier ["Machine Learning Tier"]
        FastAPI["FastAPI Microservice (Port 8000)\nPydantic v2, PyTesseract, Scikit-Learn"]
        Ollama["Ollama Engine (Port 11434)\nqwen2.5:1.5b (1.5B Parameters)"]
    end

    subgraph DataTier ["Data Tier"]
        DB[("MySQL 8.0 (Port 3306)\nTables: users, groups, expenses, receipts")]
        Storage["Local Filesystem\n(uploads/receipts/)"]
    end

    SPA -->|"REST APIs (Bearer JWT)"| SpringBoot
    SpringBoot -->|"Internal REST (X-Internal-Secret)"| FastAPI
    SpringBoot -->|"Flyway / Hibernate"| DB
    SpringBoot -->|"MultiPart / File IO"| Storage
    FastAPI -->|"Local HTTP JSON"| Ollama
    FastAPI -->|"File Read / CV2"| Storage
```

---

### Diagram 3: Natural Language Expense Splitting Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant UI as React Frontend
    participant SB as Spring Boot Backend
    participant AI as FastAPI AI Service
    participant LLM as Ollama (qwen2.5)

    User->>UI: Enter prompt: "Alex paid ₹1,200 for dinner..."
    UI->>SB: POST /api/groups/{id}/ai/interpret-split
    Note over SB: Validates JWT & Group Membership
    SB->>AI: POST /internal/v1/expenses/interpret-split (X-Internal-Secret)
    AI->>AI: Inspect for Foreign Currency Markers ($ / EUR)
    alt Foreign Currency Detected
        AI-->>SB: Return clarification_required=True
        SB-->>UI: Warning: "Foreign currency detected"
    else Valid INR Currency
        AI->>LLM: JSON Prompt with Member ID Constraints
        LLM-->>AI: Raw JSON: {amount: 1200, payer: Alex, allocations}
        AI->>AI: Validate Member IDs against Group Roster
        AI-->>SB: Structured DTO (SplitType, Shares, Confidence)
        SB-->>UI: 200 OK: InterpretSplitResponseDto
        UI->>User: Auto-populate Form (Alex ₹600, Alice ₹300, Bob ₹300)
    end
```

---

### Diagram 4: Receipt OCR & Mathematical Reconciliation Pipeline
```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant UI as React Frontend
    participant SB as Spring Boot Backend
    participant AI as FastAPI Service
    participant Tesseract as Tesseract OCR
    participant LLM as Ollama Engine

    User->>UI: Upload sample_receipt.png
    UI->>SB: POST /api/groups/{id}/receipts (Multipart)
    SB->>SB: Save to disk, create Receipt (Status: UPLOADED)
    SB-->>UI: ReceiptDto (ID, Status: UPLOADED)
    UI->>SB: POST /api/groups/{id}/receipts/{id}/extract
    SB->>AI: POST /internal/v1/receipts/extract
    AI->>Tesseract: image_to_string() Preprocessed Receipt
    Tesseract-->>AI: Raw OCR Text ($25.97, $2.14, $28.11)
    AI->>LLM: Extraction Prompt with Pydantic JSON Schema
    LLM-->>AI: Extracted Items, Subtotal, Tax, Final Total
    AI->>AI: Fallback Regex & Invariant Verification
    Note over AI: Invariant 1: sum(items) == subtotal ($25.97)<br/>Invariant 2: subtotal + tax == total ($28.11)
    AI-->>SB: Structured Extraction Payload (Status: RECONCILED)
    SB->>SB: Update Receipt in DB (Status: EXTRACTED)
    SB-->>UI: ReceiptDto (Reconciled, Discrepancy: 0.00)
```

---

### Diagram 5: Foreign Currency Protection & Ledger Boundary
```mermaid
flowchart TD
    Doc["Uploaded Document / Prompt"] --> CheckCur{"Detected Currency?"}
    CheckCur -->|"INR (₹)"| AllowReview["Permit Full Review & Ledger Posting"]
    CheckCur -->|"USD / EUR / GBP"| FlagForeign["Preserve Original Currency & Amounts"]

    FlagForeign --> ReviewUI["Display Document in Review Screen"]
    ReviewUI --> Warning["Render 'Foreign Currency Ledger Restriction' Banner"]
    Warning --> DisableConfirm["Disable 'Confirm & Create Expense' Button"]

    DisableConfirm --> ApiGuard{"Direct API POST /confirm?"}
    ApiGuard -->|"Bypass UI"| Reject422["Spring Boot Returns HTTP 422 Unprocessable Entity"]
    Reject422 --> NoLedgerChange["Ledger Untouched / Balance Unaffected"]

    AllowReview --> ConfirmBtn["User Clicks 'Confirm & Create Expense'"]
    ConfirmBtn --> PostLedger["Spring Boot Creates Expense in INR"]
```

---

### Diagram 6: Financial Invariants State Machine
```mermaid
stateDiagram-v2
    [*] --> UPLOADED : Receipt Upload
    UPLOADED --> PROCESSING : Extract Triggered
    PROCESSING --> EXTRACTED : OCR + LLM Parsing

    state EXTRACTED {
        [*] --> InvariantCheck
        InvariantCheck --> RECONCILED : sum(items)==subtotal && subtotal+tax==total
        InvariantCheck --> DISCREPANCY_DETECTED : Math Mismatch or Ambiguity
    }

    EXTRACTED --> REVIEWED : User Edits / Confirms Items
    REVIEWED --> CONFIRMED : Confirm Transaction (Pessimistic Lock)
    CONFIRMED --> [*] : Immutable Expense Created
```

---

### Diagram 7: Anomaly Detection Pipeline Flowchart
```mermaid
flowchart TD
    Req["GET /api/groups/{id}/analytics"] --> QueryExp["Query All Group Expenses"]
    QueryExp --> CountCheck{"Expense Count >= 5?"}

    CountCheck -->|"No (< 5)"| Insufficient["Return Empty Anomaly List\nAlgorithm: None"]
    CountCheck -->|"Yes (5 to 19)"| IQR["Execute Statistical IQR Baseline\nIQR = Q3 - Q1\nThreshold = Q3 + 1.5 * IQR"]
    CountCheck -->|"Yes (>= 20)"| IF["Execute Scikit-Learn Isolation Forest\nContamination = 0.05\nFit Amount + Category Vectors"]

    IQR --> FlagIQR["Identify Expenses > Threshold\nLabel: Review Suggestion"]
    IF --> FlagIF["Identify Outlier Inliers (-1)\nLabel: Review Suggestion"]

    FlagIQR --> Resp["Return GroupAnalyticsDto\nDynamic Algorithm Label"]
    FlagIF --> Resp
```

---

### Diagram 8: Pessimistic Concurrency & Idempotency Locking
```mermaid
sequenceDiagram
    autonumber
    participant ThreadA as Thread A (User Click 1)
    participant ThreadB as Thread B (Rapid Click 2)
    participant DB as MySQL Database (InnoDB)

    ThreadA->>DB: SELECT * FROM receipts WHERE id = 1 FOR UPDATE
    Note over DB: Lock acquired by Thread A
    ThreadB->>DB: SELECT * FROM receipts WHERE id = 1 FOR UPDATE
    Note over DB: Thread B waits for lock release...
    ThreadA->>ThreadA: Verify status == EXTRACTED
    ThreadA->>DB: INSERT INTO expenses (...); UPDATE receipts SET status = 'CONFIRMED'
    ThreadA->>DB: COMMIT (Releases Lock)
    Note over DB: Lock granted to Thread B
    ThreadB->>ThreadB: Verify status == CONFIRMED
    ThreadB-->>ThreadB: Throw ResponseStatusException(HttpStatus.CONFLICT, "Receipt already confirmed")
    ThreadB->>DB: ROLLBACK
```

---

### Diagram 9: Multi-Tenant Group Authorization & Membership Flow
```mermaid
flowchart TD
    Req["Incoming API Request"] --> JWT["JwtAuthenticationFilter"]
    JWT --> ValToken{"Token Valid?"}
    ValToken -->|"No"| Err401["HTTP 401 Unauthorized"]
    ValToken -->|"Yes"| ExtractUser["Extract User Entity"]

    ExtractUser --> CheckRoute{"Route requires Group Scope?"}
    CheckRoute -->|"No (e.g. /me/dashboard)"| Allow["Dispatch to Service"]
    CheckRoute -->|"Yes (/api/groups/{id}/*)"| FindMember["Check group_members Table"]

    FindMember --> IsMember{"Is User active Member of Group?"}
    IsMember -->|"No"| Err403["HTTP 403 Forbidden"]
    IsMember -->|"Yes"| Allow
```

---

### Diagram 10: Native vs Containerized Deployment Topology
```mermaid
flowchart LR
    subgraph WindowsHost ["Windows Host Native Deployment (Primary Recommended)"]
        OllamaLocal["Ollama Service (11434)"]
        MySQLLocal["MySQL 8.0 (3306)"]
        TessLocal["Tesseract-OCR (Host PATH)"]
        FastAPILocal["FastAPI (Python 3.13, 8000)"]
        SBLocal["Spring Boot (Java 21, 8080)"]
        ViteLocal["Vite Dev Server (Node, 5173)"]

        ViteLocal --> SBLocal
        SBLocal --> MySQLLocal
        SBLocal --> FastAPILocal
        FastAPILocal --> TessLocal
        FastAPILocal --> OllamaLocal
    end

    subgraph DockerTopology ["Docker Compose (Alternative Profile)"]
        DC_MySQL["mysql:8.0 Container"]
        DC_AI["ai-service Container"]
        DC_Backend["backend Container"]
        DC_Frontend["frontend Container (Nginx)"]

        DC_Frontend --> DC_Backend
        DC_Backend --> DC_MySQL
        DC_Backend --> DC_AI
        DC_AI -.->|"host.docker.internal"| OllamaLocal
    end
```

---

## 4. Security & Boundary Architecture

### Authentication & Token Flow
1. **Client to Backend**: All private endpoints require a JSON Web Token (JWT) in the `Authorization: Bearer <token>` header. Tokens are signed with HMAC-SHA256 (`jwt.secret`) and carry a 1-hour expiration timestamp.
2. **Backend to AI Microservice**: Inter-service communication between Spring Boot and FastAPI is secured via a shared pre-shared secret in the `X-Internal-Secret` header. Direct requests from unauthorized clients or public networks receive `HTTP 401 Unauthorized`.
3. **Cross-Origin Resource Sharing (CORS)**: Configured in `SecurityConfig.java` to permit browser requests originating from `http://localhost:5173` and `http://localhost:3000` with standard authorization headers.
