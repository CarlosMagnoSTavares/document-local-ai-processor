@echo off
echo 🧪 Testing Smart Upload and CPU/GPU Configuration
echo ================================================

echo.
echo 1️⃣ Testing API Root (should show v1.1.0 with new features)...
curl -X GET "http://localhost:8000/"

echo.
echo 2️⃣ Testing current compute mode...
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/config/compute"

echo.
echo 3️⃣ Testing Smart Upload with auto-detection...
curl -X POST "http://localhost:8000/upload" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Prompt: Teste de detecção automática de arquivo" ^
  -H "Format-Response: [{\"tipo_detectado\": \"\", \"ferramenta_usada\": \"\"}]" ^
  -H "Model: gemma3:1b" ^
  -F "file=@teste.jpg"

echo.
echo 4️⃣ Testing CPU mode switch...
curl -X POST "http://localhost:8000/config/compute" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Compute-Mode: cpu"

echo.
echo 5️⃣ Verifying CPU mode was set...
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/config/compute"

echo.
echo ✅ Testing completed!
echo 💡 Check Docker logs for verbose auto-detection logs:
echo    docker exec myelin-ocr-llm-local-document-ocr-api-1 tail -f /app/logs/verbose.log
pause 