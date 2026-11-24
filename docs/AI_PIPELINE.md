# Splitwise AI — Machine Learning & Vision Pipeline Specification

This document details the architecture, prompt engineering, validation logic, and local machine learning models powering Splitwise AI.

---

## 1. Local-First AI Architecture

Splitwise AI runs 100% locally on the host machine without external subscriptions, paid APIs, or cloud vendor locks:
- **Local Language Model**: Ollama serving `qwen2.5:1.5b` (1.5 billion parameters, Q4_K_M quantized, ~986 MB RAM footprint).
- **Computer Vision / OCR**: Tesseract-OCR v5 engine accessed via `pytesseract` and optimized with OpenCV image preprocessing pipelines.
- **Unsupervised Anomaly Detection**: Statistical Interquartile Range (IQR) and Scikit-Learn `IsolationForest`.
- **Validation Engine**: Pydantic v2 data models with deterministic arithmetic constraints.

```
                      +---------------------------------------+
                      |         Raw Receipt / Prompt          |
                      +---------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
             Image / Document                      Natural Language Text
                      |                                       |
                      v                                       v
          +-----------------------+               +-----------------------+
          | OpenCV Preprocessing  |               |  Foreign Currency     |
          |  (Grayscale, Thresh)  |               |  Regex Interceptor    |
          +-----------------------+               +-----------------------+
                      |                                       |
                      v                                       v
          +-----------------------+               +-----------------------+
          |     Tesseract OCR     |               | Prompt Construction   |
          |  (Raw Text Extracted) |               | (Roster ID Grounding) |
          +-----------------------+               +-----------------------+
                      |                                       |
                      +-------------------+-------------------+
                                          |
                                          v
                              +-----------------------+
                              |   Local Ollama Engine |
                              |     (qwen2.5:1.5b)    |
                              +-----------------------+
                                          |
                                          v
                              +-----------------------+
                              | Pydantic v2 Parsing   |
                              +-----------------------+
                                          |
                                          v
                              +-----------------------+
                              | Deterministic Math &  |
                              | Invariant Validation  |
                              +-----------------------+
                                          |
                                          v
                              +-----------------------+
                              | Structured JSON DTO   |
                              +-----------------------+
```

---

## 2. Receipt Vision & OCR Pipeline

### 1. OpenCV Preprocessing
Raw smartphone receipt photos suffer from uneven lighting, shadows, paper wrinkles, and low contrast. Before character recognition, the image undergoes deterministic CV preprocessing:
1. **Grayscale Conversion**: Eliminates color noise.
2. **Bilateral Filtering**: Smooths out texture while preserving sharp text edges.
3. **Adaptive Gaussian Thresholding**: Converts pixels to binary black/white based on local neighborhood illumination, isolating characters from backgrounds.
4. **Orientation Correction / Deskewing**: Normalizes rotational skew.

### 2. OCR Text Extraction
- Preprocessed images are passed to Tesseract via `pytesseract.image_to_string()`.
- The raw, unmutated text is captured and stored directly in the `raw_ocr_text` database column, providing a transparent audit trail for user inspection.

### 3. Structured Data Extraction Prompting
The raw text is formatted into a system prompt enforcing a strict JSON schema:
```json
{
  "merchant": "string",
  "receipt_date": "YYYY-MM-DD or string",
  "currency": "USD | EUR | GBP | INR",
  "currency_symbol": "$ | € | £ | ₹",
  "items": [
    {
      "description": "string",
      "quantity": 1.0,
      "unit_price": 0.0,
      "line_total": 0.0,
      "is_ambiguous": false
    }
  ],
  "subtotal": 0.0,
  "tax": 0.0,
  "total": 0.0
}
```

### 4. Mathematical Invariant Verification
The service enforces two mathematical invariants in minor units (paise / cents):

1. **Item Conservation Invariant**:
   $$\sum_{i=1}^{n} \text{line\_total}_i == \text{subtotal}$$
2. **Reconciliation Invariant**:
   $$\text{subtotal} + \text{tax} == \text{total}$$

- If both invariants evaluate to true with zero ambiguous flags, the receipt receives status `RECONCILED` with discrepancy `0.00`.
- If either invariant fails, the status is set to `DISCREPANCY_DETECTED`, the difference is calculated, and the user must explicitly verify or edit the values before confirmation.
- **Critical Safety Guard**: The system never silently mutates or forces numbers to reconcile. Extracted document evidence is preserved faithfully.

---

## 3. Natural Language Expense Splitting Pipeline

### Prompt Construction & Few-Shot Roster Grounding
When a user submits a natural-language description (e.g. `"Alex paid ₹1,200 for dinner. Alex takes 50%, Alice and Bob 25% each. Carol is excluded."`), the AI service grounds the input against the authorized group members:

```
SYSTEM PROMPT:
You are a financial parsing assistant for Splitwise AI.
Given an instruction and an authorized member roster, extract:
- description: Brief description of the expense
- total_amount: Total numeric monetary amount (in INR)
- payer_id: The member ID of the payer
- split_type: EQUAL, PERCENT, or CUSTOM
- allocations: List of participants and their shares or percentages

AUTHORIZED GROUP ROSTER:
- ID 12: Alex Morgan
- ID 13: Alice Chen
- ID 14: Bob Martinez
- ID 15: Carol Taylor

CRITICAL CONSTRAINTS:
1. ONLY use member IDs from the authorized roster above.
2. NEVER invent, hallucinate, or fabricate user IDs.
3. If an unrecognized name is mentioned, flag clarification_required = true.
4. All percentages must sum to 100.
```

### Foreign Currency Guard
Before invoking the local LLM, a regex filter scans the input for foreign currency indicators (`$`, `USD`, `dollars`, `bucks`, `€`, `EUR`, `euros`, `£`, `GBP`, `¥`, `JPY`):
- When detected, the service immediately returns `clarification_required = true` with a helpful message:
  *"Foreign currency (USD) detected. Splitwise AI currently only supports INR (₹) transactions. Please convert the amount to INR before splitting."*
- This prevents the system from misinterpreting a $50 expense as ₹50.

---

## 4. Anomaly Detection & Financial Analytics

The anomaly detection engine identifies statistical outliers in group spending without making defamatory claims of fraud. All flagged items are framed constructively as **Review Suggestions** (`REQUIRES_REVIEW`).

### Adaptive Dual-Algorithm Architecture

```
                    +------------------------------------+
                    |        Group Expense History       |
                    +------------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
             5 to 19 Expenses                        >= 20 Expenses
                   |                                       |
                   v                                       v
       +-----------------------+               +-----------------------+
       |    Statistical IQR    |               |  Scikit-Learn         |
       |       Baseline        |               |  Isolation Forest     |
       +-----------------------+               +-----------------------+
```

### 1. Statistical IQR Baseline ($5 \le N < 20$)
Used when sample size is insufficient for multi-dimensional machine learning:
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Upper Threshold} = Q_3 + 1.5 \times \text{IQR}$$
An expense with amount $A > \text{Upper Threshold}$ is flagged with reason:
*"Significantly higher than typical group spending (IQR upper bound ₹X.XX)."*

### 2. Scikit-Learn Isolation Forest ($N \ge 20$)
Used for mature groups with sufficient transaction history:
- Employs an ensemble of isolation trees (`contamination=0.05`, `random_state=42`).
- Features: Normalized expense amount and one-hot encoded category vector.
- Transactions isolated with few splittings (anomaly score $< 0$) are flagged for review.

### Dynamic Algorithm Transparency
The API response (`GroupAnalyticsDto`) and frontend UI dynamically disclose the algorithm in effect:
- `"Statistical IQR Baseline"`
- `"Scikit-Learn Isolation Forest"`
This ensures complete algorithmic transparency for users and reviewers.
