@echo off
echo 🔧 Document OCR API - Rebuild & Debug Script
echo ============================================

REM 1. Parar containers existentes
echo 🛑 Stopping existing containers...
docker-compose down -v

REM 2. Rebuild com cache limpo
echo 🔨 Building with no cache...
docker-compose build --no-cache

REM 3. Iniciar containers
echo 🚀 Starting containers...
docker-compose up -d

REM 4. Aguardar inicialização
echo ⏳ Waiting for services to start...
timeout /t 20 /nobreak >nul

REM 5. Verificar status dos containers
echo 📊 Container status:
docker-compose ps

REM 6. Testar conectividade Ollama
echo.
echo 🔗 Testing Ollama connectivity:
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Ollama is responding
    curl -s http://localhost:11434/api/tags
) else (
    echo ❌ Ollama is not responding
    echo Container logs:
    docker-compose logs --tail=50 document-ocr-api
)

REM 7. Testar API principal
echo.
echo 🌐 Testing main API:
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Main API is responding
    curl -s http://localhost:8000/health
) else (
    echo ❌ Main API is not responding
)

echo.
echo ✅ Rebuild complete! Use the following commands to debug further:
echo 📋 View all logs:       docker-compose logs -f
echo 🐛 Enter container:     docker exec -it $(docker-compose ps -q) bash
echo 🔄 Restart services:    docker-compose restart
pause 