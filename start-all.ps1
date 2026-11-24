# ==============================================================================
# Splitwise AI - Local Multi-Service Runner (Windows PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Splitwise AI Development Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 0. Load environment configuration from .env if present
if (Test-Path ".env") {
    Write-Host "`nLoading environment configuration from .env..." -ForegroundColor Gray
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $varName = $parts[0].Trim()
            $varVal = $parts[1].Trim()
            [System.Environment]::SetEnvironmentVariable($varName, $varVal, [System.EnvironmentVariableTarget]::Process)
        }
    }
    Write-Host " [OK] Environment variables loaded." -ForegroundColor Green
}

# 1. Verify Ollama
Write-Host "`n[1/4] Checking Ollama Service..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    $models = $ollamaCheck.models | ForEach-Object { $_.name }
    Write-Host " [OK] Ollama is active. Installed models: $($models -join ', ')" -ForegroundColor Green
} catch {
    Write-Host " [WARNING] Ollama is not responding at http://127.0.0.1:11434." -ForegroundColor Red
    Write-Host " Please start Ollama with: ollama serve" -ForegroundColor Yellow
}

# 2. Start Python AI Microservice (Port 8000)
Write-Host "`n[2/4] Starting AI Microservice (FastAPI on Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'ai-service'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Write-Host " [OK] AI Microservice process launched." -ForegroundColor Green

# 3. Start Spring Boot Backend (Port 8080)
Write-Host "`n[3/4] Starting Spring Boot Backend (Port 8080)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'expense-splitter-backend'; .\mvnw.cmd spring-boot:run"
Write-Host " [OK] Backend process launched." -ForegroundColor Green

# 4. Start React Frontend (Port 5173)
Write-Host "`n[4/4] Starting React Frontend (Vite on Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'frontend'; npm run dev"
Write-Host " [OK] Frontend process launched." -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  Services Started!" -ForegroundColor Green
Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8080/api" -ForegroundColor White
Write-Host "  AI Service:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Ollama:      http://127.0.0.1:11434" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
