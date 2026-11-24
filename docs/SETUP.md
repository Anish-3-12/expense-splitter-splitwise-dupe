# Splitwise AI — Complete Environment Setup & Operation Guide

This guide provides step-by-step instructions to configure, run, and test Splitwise AI on a local Windows machine.

---

## 1. Prerequisites & System Requirements

Splitwise AI is optimized to run efficiently on standard consumer hardware (including laptops with 6–8 GB RAM) without requiring paid cloud GPUs.

| Component | Minimum Version | Verified Environment | Purpose |
|:----------|:---------------:|:--------------------:|:--------|
| **OS** | Windows 10/11 | Windows 11 Pro 64-bit | Host Operating System |
| **Java Development Kit** | JDK 17+ | OpenJDK 21.0.12.1 | Spring Boot 3 Backend |
| **Python** | 3.10+ | Python 3.13.5 | FastAPI AI Microservice |
| **Node.js** | 18+ | Node.js v20.x / npm v10.x | React 19 Frontend |
| **MySQL Server** | 8.0+ | MySQL Community Server 8.0.36 | Persistent Relational Store |
| **Ollama** | 0.3+ | Ollama v0.5+ | Local Large Language Model Engine |
| **Tesseract OCR** | 5.0+ | Tesseract v5.3+ (UB-Mannheim) | Optical Character Recognition |

---

## 2. One-Time Software Installation

### 1. MySQL Database Setup
1. Ensure MySQL Server is installed and running on port `3306`.
2. Connect to MySQL via CLI or Workbench:
   ```sql
   CREATE DATABASE IF NOT EXISTS expense_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Update database credentials in your `.env` or `expense-splitter-backend/src/main/resources/application.yml` if your MySQL password differs from the default (`root / your_mysql_password`).

### 2. Ollama Local LLM
1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Open a terminal and download the recommended lightweight model:
   ```powershell
   ollama pull qwen2.5:1.5b
   ```
3. Verify the model is available:
   ```powershell
   ollama list
   ```

### 3. Tesseract OCR (Windows)
1. Download the Windows installer from [UB-Mannheim Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install to the default directory: `C:\Program Files\Tesseract-OCR\`.
3. Add `C:\Program Files\Tesseract-OCR\` to your Windows System `PATH` environment variable.
4. Verify from PowerShell:
   ```powershell
   tesseract --version
   ```

---

## 3. Launching Splitwise AI (Native Windows Method)

The verified and recommended method to run Splitwise AI is native Windows execution.

### Quick Launch via Unified Script
Open PowerShell in the repository root directory:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-all.ps1
```

---

### Manual Step-by-Step Launch (Individual Terminals)

If you prefer launching each service in its own dedicated terminal:

#### Terminal 1: Local Ollama Engine
```powershell
ollama serve
```
*(Runs on `http://127.0.0.1:11434`)*

#### Terminal 2: Python AI Microservice
```powershell
Set-Location "ai-service"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*(Runs on `http://localhost:8000`)*

#### Terminal 3: Spring Boot Financial Backend
```powershell
Set-Location "expense-splitter-backend"
.\mvnw.cmd spring-boot:run
```
*(Flyway automatically creates tables and applies migrations V1–V8. Backend runs on `http://localhost:8080`)*

#### Terminal 4: React 19 Frontend
```powershell
Set-Location "frontend"
npm install
npm run dev
```
*(Frontend runs on `http://localhost:5173`)*

---

## 4. Seeding Realistic Demonstration Data

To populate the database with realistic demo groups, participants, categorized expenses, and settlement records:
```powershell
python scripts/seed_demo_data.py
```

### Pre-Configured Demonstration Credentials:
- **Email**: `demo.reviewer@splitwise.ai`
- **Password**: `Password123!`
- **User Name**: Alex Morgan (User ID: 12)
- **Active Groups**:
  - `Apartment 4B Roommates` (Household expenses, utilities, TV purchase)
  - `Lake Tahoe Ski Trip` (Travel lodging, AWD rental, lift tickets)
  - `Weekend Foodies Club` (Dining, craft beer, food festivals)

---

## 5. Verification & Automated Test Suites

### 1. Spring Boot Backend Tests (35 Tests)
```powershell
Set-Location "expense-splitter-backend"
.\mvnw.cmd test
```
*Executes unit and integration tests covering security, calculations, currency rejection, and receipt idempotency.*

### 2. Python AI Service Tests (38 Tests)
```powershell
Set-Location "ai-service"
python -m pytest tests -v
```
*Tests OCR fallback parsing, mathematical invariant verification, foreign currency prompt guards, and isolation forest anomaly detection.*

### 3. Frontend Production Build
```powershell
Set-Location "frontend"
npm run build
```
*Verifies complete JSX compilation, asset bundling, and zero syntax errors.*

### 4. End-to-End Live Integration Verification
```powershell
python scripts/verify_live_api.py
```
*Validates authentication, group listing, analytics calculation, and IQR anomaly detection on live running servers.*

---

## 6. Troubleshooting Common Issues

### 1. Port Collisions
- **Port 8080**: Check if an existing Tomcat or Jenkins service is running (`Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess`).
- **Port 8000**: Check if another Python development server is active.
- **Port 5173**: Vite will automatically offer port 5174 if 5173 is occupied.

### 2. Ollama CPU Latency
On machines without dedicated NVIDIA CUDA GPUs, Ollama runs inference on CPU. A 1.5B model takes ~30–45s for complex receipt parsing.
- If timeouts occur, ensure `INFERENCE_TIMEOUT=90` or `120` in `.env`.
- Do not close or suspend the terminal running `ollama serve`.

### 3. Tesseract Path Resolution
If the AI service logs report `TesseractNotFoundError`:
- Verify `tesseract.exe` exists in `C:\Program Files\Tesseract-OCR\`.
- Set the environment variable in `.env`:
  ```
  TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```

---

## 7. Containerized Deployment Note (Docker)

Docker configuration (`docker-compose.yml`, `Dockerfile` for each service) is included in the repository for reference. However, **native Windows execution is the primary verified demonstration deployment**. Running local Ollama and GPU hardware passthrough inside Docker Desktop on Windows requires complex WSL2 virtualization flags, whereas native deployment runs reliably and requires minimal RAM overhead.
