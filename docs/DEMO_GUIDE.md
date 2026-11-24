# Splitwise AI — 5-to-8 Minute Live Technical Demonstration Guide

This guide provides a structured, time-stamped demonstration script designed for technical interviews, hiring manager reviews, and engineering team walkthroughs.

---

## 1. Demo Setup Checklist

Before beginning the presentation, verify that all services are active:
- [x] MySQL 8.0 running on port `3306`
- [x] Ollama daemon running on port `11434` with `qwen2.5:1.5b`
- [x] Python AI microservice running on port `8000`
- [x] Spring Boot backend running on port `8080`
- [x] React frontend running on port `5173`
- [x] Demo data seeded (`python scripts/seed_demo_data.py`)

**Demo Credentials**:
- **URL**: `http://localhost:5173`
- **Email**: `demo.reviewer@splitwise.ai`
- **Password**: `Password123!`
- **Presenter Name**: Alex Morgan

---

## 2. Minute-by-Minute Demonstration Script

### Minute 0:00 – 1:00 | Dashboard & Financial Position Overview
1. Open the browser to `http://localhost:5173` and log in.
2. **Talking Points**:
   - *"Welcome to Splitwise AI. What you see here is the user dashboard, designed to give users an immediate view of their personal financial state."*
   - Point to the top KPI cards: **Total Spent**, **Total You are Owed**, and **Total You Owe**.
   - Note the **₹ (INR)** monetary formatting standardized across all views.
   - Point out the active groups: **Apartment 4B Roommates**, **Lake Tahoe Ski Trip**, and **Weekend Foodies Club**.
   - *"Notice how clean and responsive the layout is, utilizing Material UI v7."*

---

### Minute 1:00 – 2:30 | Natural Language Expense Splitting with Local LLM
1. Click **Add Expense** in the top navigation bar.
2. Select Group: **Apartment 4B Roommates**.
3. In the **AI Quick Split** input field, paste or type:
   ```text
   Alex paid 1200 for dinner. Alex takes 50 percent, Alice and Bob take 25 percent each. Carol is excluded.
   ```
4. Click **Interpret & Fill**.
5. **Talking Points While Processing (~20–30s on CPU)**:
   - *"The frontend is calling our local Python FastAPI microservice, which prompts an onboard Ollama instance running the quantized 1.5B parameter Qwen 2.5 model."*
   - *"Notice what the AI does not do: it does not fabricate user IDs. The microservice injects the authorized group members (Alex, Alice, Bob, Carol) into the system prompt, forcing the LLM to ground its allocations strictly to valid database IDs."*
6. Show the result:
   - Description: **Dinner**
   - Amount: **₹1,200.00**
   - Split Type: **PERCENT**
   - Allocations: **Alex (50% = ₹600)**, **Alice (25% = ₹300)**, **Bob (25% = ₹300)**. Carol is omitted.
7. **Demonstrate Safety Guard (Currency Protection)**:
   - Paste: `"I paid $50 for lunch"` and click Interpret.
   - Show the alert: *"Foreign currency (USD) detected. The ledger operates strictly in INR."*
   - *"The system refuses to silently convert $50 into ₹50, protecting financial ledger integrity."*

---

### Minute 2:30 – 4:30 | Receipt OCR & Mathematical Reconciliation
1. Navigate to **Receipt Scanner** in the navbar.
2. Select Group: **Apartment 4B Roommates**.
3. Upload `sample_receipt.png` (or drag and drop into the dropzone).
4. Click **Extract Receipt Data**.
5. **Talking Points While Extracting (~35–45s on CPU)**:
   - *"Here, our vision pipeline executes OpenCV image preprocessing (adaptive thresholding, noise reduction) followed by Tesseract OCR to extract raw character data."*
   - *"The raw text is then parsed into structured line items, quantities, and prices."*
6. Inspect the Extracted Data:
   - Subtotal: **$25.97**
   - Tax: **$2.14**
   - Total: **$28.11**
   - Line items: 5 items summing to **$25.97**.
7. **Highlight the Reconciliation Badge**:
   - Status: **RECONCILED (Discrepancy: $0.00)**.
   - *"Notice our two financial invariants: Invariant 1 verifies that the sum of the line items ($25.97) equals the subtotal. Invariant 2 verifies that subtotal + tax ($25.97 + $2.14) equals the total ($28.11)."*
8. **Highlight Multi-Currency Safety & Restriction**:
   - Point out the warning banner: **Foreign Currency Ledger Restriction (USD)**.
   - Note the **Confirm & Create Expense** button is disabled with text: `"Posting Restricted (USD Ledger Mismatch)"`.
   - *"Our architecture preserves document fidelity—we extract and display the true USD amounts and currency symbol. But because the underlying financial ledger is INR-only, we prevent foreign receipts from being posted directly without an exchange conversion."*

---

### Minute 4:30 – 5:45 | Debt Settlements & Invariant Verification
1. Click **Settlements** in the navbar.
2. Select Group: **Apartment 4B Roommates**.
3. **Talking Points**:
   - *"Notice our responsive two-column layout on desktop: the 'Who Owes Who' balance matrix on the left (5/12 width) and 'Settlement History' on the right (7/12 width)."*
   - Look at the net balances:
     - Alex Morgan: **+₹1,593.70** (Creditor)
     - Alice Chen: **-₹545.50** (Debtor)
     - Bob Martinez: **-₹661.35** (Debtor)
     - Carol Taylor: **-₹386.85** (Debtor)
   - Invariant Check: $1593.70 - 545.50 - 661.35 - 386.85 = 0.00$.
4. Click **Record Settlement**:
   - Payer: **Alice Chen**, Recipient: **Alex Morgan**, Amount: **₹545.50**, Note: *"Paid via UPI"*.
   - Click Record.
   - Observe Alice Chen's balance immediately settle to **₹0.00**.

---

### Minute 5:45 – 7:00 | Group Analytics & Unsupervised Anomaly Detection
1. Click **Analytics** in the navbar.
2. Select Group: **Apartment 4B Roommates**.
3. **Talking Points**:
   - Point out the spending summary metrics: **Total Spending (₹3,284.70)**, **Average Expense (₹547.45)**.
   - Point to the dynamic badge: **Algorithm: Statistical IQR Baseline**.
   - *"Our system features adaptive anomaly detection. For groups with 5 to 19 expenses, it executes a robust statistical Interquartile Range (IQR) baseline. For groups with 20 or more expenses, it automatically transitions to a Scikit-Learn Isolation Forest."*
4. Scroll to **Unusual Spending / Anomalies Detected**:
   - Highlight the flagged card: **November Apartment Rent (₹2,400.00)**.
   - Category: **Housing & Rent**.
   - Label: **Review Suggestion (REQUIRES_REVIEW)**.
   - Reason: *"Significantly higher than typical group spending (IQR upper bound ₹759.44)."*
   - *"Crucially, the UI frames this as an actionable review suggestion rather than making an accusatory claim of fraud."*

---

### Minute 7:00+ | Conclusion & Architectural Summary
- *"To summarize: Splitwise AI demonstrates how to integrate modern AI capabilities (local LLMs, computer vision, machine learning) into a production-grade enterprise software architecture. We maintain strict separation of concerns: Spring Boot remains the ultimate authority for financial invariants, security, and persistence, while Python and Ollama act as specialized advisory microservices."*
- Invite questions from the interviewer.
