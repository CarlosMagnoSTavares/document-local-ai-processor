@echo off
echo 🎉 Final Verification - Model Download Fixed
echo ============================================

echo.
echo 1️⃣ Testing INVALID model (should show clear error)...
curl -X POST "http://localhost:8000/models/download" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Model-Name: invalid:model"

echo.
echo 2️⃣ Testing VALID model download with verification...
curl -X POST "http://localhost:8000/models/download" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Model-Name: qwen2:1.5b"

echo.
echo 3️⃣ Listing all models (should include downloaded models)...
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/models/list"

echo.
echo 4️⃣ Testing upload with downloaded model...
curl -X POST "http://localhost:8000/upload" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Prompt: Teste final de verificação" ^
  -H "Format-Response: [{\"status\": \"funcionando\"}]" ^
  -H "Model: qwen2:1.5b" ^
  -F "file=@teste.jpg"

echo.
echo ✅ All tests completed!
echo.
echo 📋 Summary of fixes:
echo  • Model download now verifies if model actually exists in Ollama
echo  • Clear error messages for invalid models
echo  • Downloaded models appear correctly in list
echo  • Downloaded models work in upload API
pause 