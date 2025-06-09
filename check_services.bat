@echo off
echo 🔍 Document OCR API - Service Check
echo ==================================

REM 1. Verificar se containers estão rodando
echo 📦 Container Status:
docker-compose ps
echo.

REM 2. Verificar API principal
echo 🌐 Main API Health Check:
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Main API is responding
    curl -s http://localhost:8000/health
) else (
    echo ❌ Main API is not responding on port 8000
)
echo.

REM 3. Verificar Ollama
echo 🤖 Ollama Service Check:
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Ollama is responding
    echo 📋 Available models:
    curl -s http://localhost:11434/api/tags
) else (
    echo ❌ Ollama is not responding on port 11434
    echo 🔧 Try: docker-compose restart
)
echo.

REM 4. Logs recentes
echo 📋 Recent Logs (last 10 lines):
docker-compose logs --tail=10 document-ocr-api
echo.

echo 🔧 Quick Commands:
echo   📊 Full status:     docker-compose ps
echo   📋 All logs:        docker-compose logs -f
echo   🔄 Restart:         docker-compose restart
echo   🛠️ Rebuild:         rebuild_and_debug.bat
pause 