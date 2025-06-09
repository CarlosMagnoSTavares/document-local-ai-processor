# 🧪 GUIA DE TESTES MANUAIS - Document OCR LLM API v1.5

## 🎯 CONFIGURAÇÃO INICIAL

**Credenciais de Teste:**
- API Key: `myelin-ocr-llm-2024-super-secret-key`
- Gemini API Key: `AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g`
- Base URL: `http://localhost:8000`
- Debug Mode: `debug: 1` (sempre ativo)

## 📋 LISTA DE TESTES SISTEMÁTICOS

### **1. STATUS & INFORMATION TESTS**

#### 1.1 Health Check ✅
```bash
curl -s http://localhost:8000/health
```
**Resultado esperado:** `{"status": "healthy", "message": "Document OCR LLM API is running"}`

#### 1.2 API Information 📖
```bash
curl -s http://localhost:8000/
```
**Resultado esperado:** JSON com endpoints e headers necessários

---

### **2. MODEL MANAGEMENT TESTS**

#### 2.1 List Ollama Models 🏠
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
http://localhost:8000/models/list
```
**Resultado esperado:** Lista de modelos Ollama instalados

#### 2.2 List Gemini Models 🌟
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Gemini-API-Key: AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g" \
http://localhost:8000/models/gemini
```
**Resultado esperado:** Lista dinâmica de modelos Gemini disponíveis

#### 2.3 Download Ollama Model (Opcional) 📥
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Model-Name: qwen2:0.5b" \
http://localhost:8000/models/download
```
**Resultado esperado:** Início do download do modelo

---

### **3. SMART UPLOAD TESTS**

#### 3.1 Preparação - Criar Arquivo de Teste
```bash
echo "Test document content for OCR processing. CNPJ: 12.345.678/0001-90" > test_document.txt
```

#### 3.2 Ollama Upload (Local) 🏠
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Prompt: Extract all information from this document including any CNPJ" \
-H "Format-Response: [{\"content\": \"\", \"cnpj\": \"\"}]" \
-H "Model: gemma3:1b" \
-H "AI-Provider: ollama" \
-H "debug: 1" \
-F "file=@test_document.txt" \
http://localhost:8000/upload
```
**Resultado esperado:** `{"status": "success", "document_id": X, "filename": "test_document.txt"}`
**📝 Anote o document_id retornado!**

#### 3.3 Gemini Upload (Cloud) 🌟
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Prompt: Extract all information from this document including any CNPJ" \
-H "Format-Response: [{\"content\": \"\", \"cnpj\": \"\"}]" \
-H "Model: gemini-2.0-flash" \
-H "AI-Provider: gemini" \
-H "Gemini-API-Key: AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g" \
-H "debug: 1" \
-F "file=@test_document.txt" \
http://localhost:8000/upload
```
**Resultado esperado:** `{"status": "success", "document_id": Y, "filename": "test_document.txt"}`

---

### **4. MONITOR PROCESSING TESTS**

#### 4.1 Queue Status 📊
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
http://localhost:8000/queue
```
**Resultado esperado:** Lista de documentos com status de processamento

#### 4.2 Queue Status with Debug 🔧
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "debug: 1" \
http://localhost:8000/queue
```
**Resultado esperado:** Lista com informações detalhadas de debug

---

### **5. GET RESULTS TESTS**

**⚠️ Substitua `{document_id}` pelo ID retornado no upload**

#### 5.1 Get Document Response 📄
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
http://localhost:8000/response/{document_id}
```
**Resultado esperado:** Resposta processada do documento

#### 5.2 Get Document Response with Debug 🔧
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "debug: 1" \
http://localhost:8000/response/{document_id}
```
**Resultado esperado:** Resposta com debug detalhado:
- `1_extracted_content`: Conteúdo extraído via OCR
- `2_prompt_sent_to_llm`: Prompt completo enviado ao LLM
- `3_raw_llm_response`: Resposta bruta do LLM

---

### **6. DEBUG & DIAGNOSTICS TESTS**

#### 6.1 Comprehensive Document Debug 🔍
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
http://localhost:8000/debug/document/{document_id}
```
**Resultado esperado:** Diagnóstico completo com:
- File system checks
- Database consistency
- Extraction verification
- Processing status
- Real-time re-extraction test

---

### **7. COMPUTE CONFIGURATION TESTS**

#### 7.1 Get Current Compute Mode 🔍
```bash
curl -s -H "Key: myelin-ocr-llm-2024-super-secret-key" \
http://localhost:8000/config/compute
```
**Resultado esperado:** Modo atual (CPU/GPU)

#### 7.2 Set CPU Mode 💻
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Compute-Mode: cpu" \
http://localhost:8000/config/compute
```
**Resultado esperado:** Confirmação da configuração

#### 7.3 Set GPU Mode 🚀
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Compute-Mode: gpu" \
http://localhost:8000/config/compute
```
**Resultado esperado:** Confirmação da configuração

---

### **8. ERROR TESTING**

#### 8.1 Invalid API Key ❌
```bash
curl -s -H "Key: invalid-key" \
http://localhost:8000/queue
```
**Resultado esperado:** HTTP 401 Unauthorized

#### 8.2 Missing Gemini API Key ❌
```bash
curl -s -X POST \
-H "Key: myelin-ocr-llm-2024-super-secret-key" \
-H "Prompt: Test" \
-H "Format-Response: {}" \
-H "Model: gemini-2.0-flash" \
-H "AI-Provider: gemini" \
-F "file=@test_document.txt" \
http://localhost:8000/upload
```
**Resultado esperado:** HTTP 400 - "Gemini-API-Key header is required"

---

## 🚀 SCRIPTS AUTOMATIZADOS

### Para Windows:
```cmd
test_api.bat
```

### Para Linux/Mac:
```bash
./test_api.sh
```

### Verificação de Serviços:
```bash
# Windows
check_services.bat

# Linux/Mac
./check_services.sh
```

### Rebuild Completo:
```bash
# Windows
rebuild_and_debug.bat

# Linux/Mac
./rebuild_and_debug.sh
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ **TODOS OS TESTES DEVEM PASSAR:**

1. **Health Check**: API respondendo
2. **Model Lists**: Ollama e Gemini retornando modelos
3. **Uploads**: Ambos providers (Ollama + Gemini) funcionando
4. **Queue**: Status correto dos documentos
5. **Results**: Respostas com e sem debug
6. **Debug**: Diagnósticos detalhados
7. **Config**: Mudanças de CPU/GPU
8. **Errors**: Tratamento correto de erros

### 🔍 **VALIDAÇÕES ESPECÍFICAS:**

- **Debug Response deve conter:**
  - `1_extracted_content`: Não vazio
  - `2_prompt_sent_to_llm`: Prompt completo
  - `3_raw_llm_response`: Resposta do LLM

- **Queue Status deve mostrar:**
  - `COMPLETED` para documentos processados
  - Não deve ter `ERROR` (exceto testes de erro)

- **Gemini Integration:**
  - Lista de modelos dinâmica
  - Upload funcionando com chave API
  - Modelos avançados (gemini-2.0-flash, etc.)

---

## 🐛 TROUBLESHOOTING

### Se algum teste falhar:

1. **Verificar Docker:**
```bash
docker-compose ps
docker-compose logs -f
```

2. **Restart Services:**
```bash
docker-compose restart
```

3. **Rebuild Completo:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

4. **Verificar Ollama:**
```bash
curl http://localhost:11434/api/tags
```

5. **Logs Detalhados:**
```bash
docker-compose logs document-ocr-api | grep -E "(ERROR|CRITICAL|❌)"
```

---

**Data de Atualização**: 09/06/2025  
**Versão**: 1.5  
**Status**: ✅ Pronto para testes 