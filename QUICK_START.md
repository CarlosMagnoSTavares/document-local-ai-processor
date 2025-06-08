# 🚀 Quick Start Guide

## Para começar rapidamente:

### 1. No Windows:
```batch
# Execute o script de build
build_and_run.bat
```

### 2. No Linux/Mac:
```bash
# Torne os scripts executáveis
chmod +x *.sh

# Execute o build
docker-compose up --build
```

### 3. Teste a API:
```batch
# Windows
test_api.bat

# Linux/Mac  
./test_api.sh
```

## URLs importantes:
- **API**: http://localhost:8000
- **Health**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

## API Key:
```
myelin-ocr-llm-2024-super-secret-key
```

## Exemplo de uso:
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Extraia o CNPJ deste documento" \
  -H "Format-Response: [{\"CNPJ\": \"\"}]" \
  -H "Model: gemma3:1b" \
  -F "file=@teste.jpg"
```

## ⚠️ Primeira execução:
- Aguarde 5-10 minutos para download do modelo Ollama
- Verifique os logs: `docker-compose logs -f`

## 🛑 Para parar:
```bash
docker-compose down
``` 