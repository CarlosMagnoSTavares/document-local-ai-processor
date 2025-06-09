@echo off
echo 🧪 Testing Improved Model Download Endpoint
echo ==========================================

echo.
echo 1️⃣ Testing invalid model (should show clear error)...
curl -X POST "http://localhost:8000/models/download" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Model-Name: llama3:4b"

echo.
echo 2️⃣ Testing another invalid model...
curl -X POST "http://localhost:8000/models/download" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Model-Name: invalid:model"

echo.
echo 3️⃣ Testing valid model (qwen2:0.5b - small and fast)...
curl -X POST "http://localhost:8000/models/download" ^
  -H "Key: myelin-ocr-llm-2024-super-secret-key" ^
  -H "Model-Name: qwen2:0.5b"

echo.
echo 4️⃣ Listing all available models...
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/models/list"

echo.
echo ✅ Testing completed!
echo.
echo 📋 Valid model examples from the documentation:
echo  • llama3:8b, llama3:70b (Meta LLaMA 3)
echo  • gemma2:2b, gemma2:9b, gemma2:27b (Google Gemma 2)
echo  • mistral:7b, mistral:instruct (Mistral AI)
echo  • qwen2:0.5b, qwen2:1.5b, qwen2:7b (Alibaba Qwen 2)
echo  • phi3:mini, phi3:medium (Microsoft Phi-3)
pause 