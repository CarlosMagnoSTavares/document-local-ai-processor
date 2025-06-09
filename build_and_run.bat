@echo off
echo 🚀 Building and Running Document OCR LLM API...
echo.

:: Check if Docker is running
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running!
    echo Please install Docker Desktop and make sure it's running.
    pause
    exit /b 1
)

echo ✅ Docker is available

:: Stop and remove existing container
echo 🛑 Stopping existing containers...
docker-compose down 2>nul

:: Build and start the container
echo 🔨 Building Docker image...
docker-compose build

if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo ✅ Build completed successfully

echo 🚀 Starting containers...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Failed to start containers!
    pause
    exit /b 1
)

echo ✅ Containers started successfully!
echo.
echo 🌐 API will be available at: http://localhost:8000
echo 📊 Health check: http://localhost:8000/health
echo 🤖 Ollama: http://localhost:11434
echo.
echo 📝 Logs: docker-compose logs -f
echo 🛑 Stop: docker-compose down
echo.
echo ⏳ Please wait 5-10 minutes for initial setup (downloading Ollama model)...
echo.

:: Wait for API to be ready
echo 🔄 Waiting for API to be ready...
timeout /t 30 /nobreak >nul

:: Test health endpoint
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  API not ready yet. Check logs with: docker-compose logs -f
) else (
    echo ✅ API is ready!
)

echo.
echo 🧪 To test the API, run: test_api.bat
echo.
pause 