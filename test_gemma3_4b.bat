@echo off
echo 🧪 Testing gemma3:4b Model
echo ==========================

echo.
echo 1️⃣ Listing models (should include gemma3:4b)...
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/models/list"

echo.
echo 2️⃣ Testing upload with gemma3:4b model...
curl -X POST "http://localhost:8000/upload" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Prompt: Teste com o modelo gemma3:4b" ^
  -H "Format-Response: [{\"resultado\": \"teste\"}]" ^
  -H "Model: gemma3:4b" ^
  -F "file=@teste.jpg"

echo.
echo ✅ Test completed!
pause 