@echo off
echo 🤖 Testing New Model (qwen2:0.5b)
echo ================================
echo.

set API_URL=http://localhost:8000
set API_KEY=myelin-ocr-llm-2024-super-secret-key
set TEST_FILE=teste.jpg

:: Test 1: List models
echo 1️⃣ Testing models list...
curl -X GET "%API_URL%/models/list" ^
    -H "Key: %API_KEY%"
echo.
echo.

:: Test 2: Upload with new model
echo 2️⃣ Testing upload with qwen2:0.5b model...
if exist "%TEST_FILE%" (
    echo Uploading %TEST_FILE% with qwen2:0.5b...
    curl -X POST "%API_URL%/upload" ^
        -H "Key: %API_KEY%" ^
        -H "Prompt: Analise este documento e extraia informações importantes de forma detalhada" ^
        -H "Format-Response: [{\"tipo_documento\": \"\", \"informacoes_principais\": \"\", \"dados_especificos\": \"\"}]" ^
        -H "Model: qwen2:0.5b" ^
        -F "file=@%TEST_FILE%"
    echo.
    echo 📄 Document uploaded with new model! Check the queue status for processing updates.
) else (
    echo ❌ Test file '%TEST_FILE%' not found!
)
echo.

:: Test 3: Check queue status
echo 3️⃣ Testing queue status...
timeout /t 5 /nobreak >nul
curl -X GET "%API_URL%/queue" ^
    -H "Key: %API_KEY%"
echo.
echo.

:: Test 4: Wait and check response
echo 4️⃣ Waiting for processing and checking response...
timeout /t 10 /nobreak >nul
curl -X GET "%API_URL%/response/2" ^
    -H "Key: %API_KEY%"
echo.
echo.

echo ✅ New model testing completed!
echo.
pause 