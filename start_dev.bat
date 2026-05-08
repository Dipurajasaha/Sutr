@echo off
setlocal

echo =========================================
echo      Starting Sutr AI Dev Environment
echo =========================================

echo Cleaning up any stale service windows...
taskkill /FI "WINDOWTITLE eq SUTR_FRONTEND" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_API_GATEWAY" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_UPLOAD" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_CHAT" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_PROCESSING" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_VECTOR" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_MEDIA" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Summary Service" /T /F >nul 2>&1

echo 1. Starting PostgreSQL Database...
docker-compose up -d postgres

echo 2. Starting React Frontend...
start "SUTR_FRONTEND" cmd /k "cd frontend && npm run dev"

echo 3. Starting API Gateway...
start "SUTR_API_GATEWAY" cmd /k "call venv\Scripts\activate && cd backend\services\api-gateway && uvicorn app.main:app --port 8000 --reload"

echo 4. Starting Upload Service...
start "SUTR_UPLOAD" cmd /k "call venv\Scripts\activate && cd backend\services\upload-service && uvicorn app.main:app --port 8001 --reload"

echo 5. Starting Chat Service...
start "SUTR_CHAT" cmd /k "call venv\Scripts\activate && cd backend\services\chat-service && uvicorn app.main:app --port 8004 --reload"

echo 6. Starting Processing Service...
start "SUTR_PROCESSING" cmd /k "call venv\Scripts\activate && cd backend\services\processing-service && uvicorn app.main:app --port 8003 --reload"

echo 7. Starting Vector Service...
start "SUTR_VECTOR" cmd /k "call venv\Scripts\activate && cd backend\services\vector-service && uvicorn app.main:app --port 8005 --reload"

echo 8. Starting Summary Service (Port 8006)...
start "Summary Service" cmd /k "call venv\Scripts\activate && cd backend\services\summary-service && uvicorn app.main:app --port 8006 --reload"

echo 9. Starting Media Service (Port 8007)...
start "SUTR_MEDIA" cmd /k "call venv\Scripts\activate && cd backend\services\media-service && uvicorn app.main:app --port 8007 --reload"

echo.
echo =========================================
echo Service URLs
echo =========================================
echo Frontend:       http://localhost:5173
echo API Gateway:    http://localhost:8000
echo Upload Service: http://localhost:8001
echo Chat Service:   http://localhost:8004
echo Processing:     http://localhost:8003
echo Vector:         http://localhost:8005
echo Summary:        http://localhost:8006
echo Media:          http://localhost:8007
echo =========================================

echo.
echo Press CTRL+C to stop ALL services...
pause >nul

:cleanup
echo.
echo Closing all Sutr service windows...

taskkill /FI "WINDOWTITLE eq SUTR_FRONTEND" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_API_GATEWAY" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_UPLOAD" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_CHAT" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_PROCESSING" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_VECTOR" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SUTR_MEDIA" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Summary Service" /T /F >nul 2>&1

echo Stopping PostgreSQL container...
docker-compose stop postgres

echo Done.
exit