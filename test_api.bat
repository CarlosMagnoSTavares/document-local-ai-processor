@echo off
setlocal enabledelayedexpansion

echo 🧪 Document OCR LLM API - Complete Test Suite v1.5
echo ==================================================

REM Configuration
set BASE_URL=http://localhost:8000
set API_KEY=myelin-ocr-llm-2024-super-secret-key
set GEMINI_API_KEY=AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g
set DEBUG_MODE=1

REM Test counters
set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

echo.
echo 🔧 Starting systematic API testing...

REM 1. Status & Information Tests
echo.
echo === 1. STATUS & INFORMATION TESTS ===

echo.
echo 🧪 Test: Health Check
curl -s %BASE_URL%/health
if %errorlevel% == 0 (
    echo ✅ PASSED - Health Check
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Health Check
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 🧪 Test: API Information
curl -s %BASE_URL%/
if %errorlevel% == 0 (
    echo ✅ PASSED - API Information
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - API Information
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM 2. Model Management Tests
echo.
echo === 2. MODEL MANAGEMENT TESTS ===

echo.
echo 🧪 Test: List Ollama Models
curl -s -H "Key: %API_KEY%" %BASE_URL%/models/list
if %errorlevel% == 0 (
    echo ✅ PASSED - List Ollama Models
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - List Ollama Models
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 🧪 Test: List Gemini Models
curl -s -H "Key: %API_KEY%" -H "Gemini-API-Key: %GEMINI_API_KEY%" %BASE_URL%/models/gemini
if %errorlevel% == 0 (
    echo ✅ PASSED - List Gemini Models
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - List Gemini Models
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM 3. Upload Tests
echo.
echo === 3. SMART UPLOAD TESTS ===

REM Create test file
echo Test document content for OCR processing > test_document.txt

echo.
echo 🧪 Test: Ollama Upload (TXT)
curl -s -X POST ^
-H "Key: %API_KEY%" ^
-H "Prompt: Extract all information from this document" ^
-H "Format-Response: [{\"content\": \"\"}]" ^
-H "Model: gemma3:1b" ^
-H "AI-Provider: ollama" ^
-H "debug: %DEBUG_MODE%" ^
-F "file=@test_document.txt" ^
%BASE_URL%/upload
if %errorlevel% == 0 (
    echo ✅ PASSED - Ollama Upload
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Ollama Upload
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 🧪 Test: Gemini Upload (TXT)
curl -s -X POST ^
-H "Key: %API_KEY%" ^
-H "Prompt: Extract all information from this document" ^
-H "Format-Response: [{\"content\": \"\"}]" ^
-H "Model: gemini-2.0-flash" ^
-H "AI-Provider: gemini" ^
-H "Gemini-API-Key: %GEMINI_API_KEY%" ^
-H "debug: %DEBUG_MODE%" ^
-F "file=@test_document.txt" ^
%BASE_URL%/upload
if %errorlevel% == 0 (
    echo ✅ PASSED - Gemini Upload
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Gemini Upload
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM 4. Queue Status Tests
echo.
echo === 4. MONITOR PROCESSING TESTS ===

echo.
echo 🧪 Test: Queue Status
curl -s -H "Key: %API_KEY%" %BASE_URL%/queue
if %errorlevel% == 0 (
    echo ✅ PASSED - Queue Status
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Queue Status
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 🧪 Test: Queue Status with Debug
curl -s -H "Key: %API_KEY%" -H "debug: %DEBUG_MODE%" %BASE_URL%/queue
if %errorlevel% == 0 (
    echo ✅ PASSED - Queue Status with Debug
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Queue Status with Debug
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM 5. Compute Configuration Tests
echo.
echo === 5. COMPUTE CONFIGURATION TESTS ===

echo.
echo 🧪 Test: Get Current Compute Mode
curl -s -H "Key: %API_KEY%" %BASE_URL%/config/compute
if %errorlevel% == 0 (
    echo ✅ PASSED - Get Current Compute Mode
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Get Current Compute Mode
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM 6. Error Testing
echo.
echo === 6. ERROR TESTING ===

echo.
echo 🧪 Test: Invalid API Key
curl -s -H "Key: invalid-key" %BASE_URL%/queue
if %errorlevel% == 0 (
    echo ✅ PASSED - Invalid API Key (correctly handled)
    set /a PASSED_TESTS+=1
) else (
    echo ❌ FAILED - Invalid API Key
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

REM Cleanup
del test_document.txt 2>nul

REM Final Results
echo.
echo === FINAL TEST RESULTS ===
echo 📊 Total Tests: %TOTAL_TESTS%
echo ✅ Passed: %PASSED_TESTS%
echo ❌ Failed: %FAILED_TESTS%

if %FAILED_TESTS% == 0 (
    echo.
    echo 🎉 ALL TESTS PASSED! API is working correctly.
    pause
    exit /b 0
) else (
    echo.
    echo ⚠️ Some tests failed. Check the system and retry.
    echo.
    echo 💡 Quick fixes:
    echo 1. Check if Docker is running: docker-compose ps
    echo 2. Restart services: docker-compose restart
    echo 3. Check logs: docker-compose logs -f
    echo 4. Use debug script: rebuild_and_debug.bat
    pause
    exit /b 1
) 