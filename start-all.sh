#!/usr/bin/env bash
# ==============================================================================
# Splitwise AI - Local Multi-Service Runner (Bash)
# ==============================================================================

set -e

echo -e "\033[1;36m==========================================================\033[0m"
echo -e "\033[1;36m  Starting Splitwise AI Development Platform\033[0m"
echo -e "\033[1;36m==========================================================\033[0m"

# 0. Load environment configuration from .env if present
if [ -f .env ]; then
    echo -e "\n\033[0;37mLoading environment configuration from .env...\033[0m"
    set -a
    source .env
    set +a
    echo -e "\033[1;32m [OK] Environment variables loaded.\033[0m"
fi

# 1. Check Ollama
echo -e "\n\033[1;33m[1/4] Checking Ollama Service...\033[0m"
if curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
    echo -e "\033[1;32m [OK] Ollama is active on http://127.0.0.1:11434\033[0m"
else
    echo -e "\033[1;31m [WARNING] Ollama is not responding at http://127.0.0.1:11434\033[0m"
    echo -e "\033[1;33m Start it in another terminal with: ollama serve\033[0m"
fi

# 2. Start Python AI Microservice
echo -e "\n\033[1;33m[2/4] Starting AI Microservice (Port 8000)...\033[0m"
(cd ai-service && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
PID_AI=$!
echo -e "\033[1;32m [OK] AI Microservice started with PID $PID_AI\033[0m"

# 3. Start Spring Boot Backend
echo -e "\n\033[1;33m[3/4] Starting Spring Boot Backend (Port 8080)...\033[0m"
(cd expense-splitter-backend && ./mvnw spring-boot:run) &
PID_BACKEND=$!
echo -e "\033[1;32m [OK] Backend started with PID $PID_BACKEND\033[0m"

# 4. Start React Frontend
echo -e "\n\033[1;33m[4/4] Starting Frontend (Port 5173)...\033[0m"
(cd frontend && npm run dev) &
PID_FRONTEND=$!
echo -e "\033[1;32m [OK] Frontend started with PID $PID_FRONTEND\033[0m"

trap "kill $PID_AI $PID_BACKEND $PID_FRONTEND 2>/dev/null || true" EXIT

echo -e "\n\033[1;32m==========================================================\033[0m"
echo -e "  All services running! Press Ctrl+C to terminate all."
echo -e "  Frontend:    http://localhost:5173"
echo -e "  Backend API: http://localhost:8080/api"
echo -e "  AI Service:  http://127.0.0.1:8000/docs"
echo -e "\033[1;32m==========================================================\033[0m"

wait
