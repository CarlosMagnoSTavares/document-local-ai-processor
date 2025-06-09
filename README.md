# 🧠 Document OCR LLM API

API escalável, segura e leve para análise de documentos com auxílio de modelos de linguagem locais (Ollama) e em nuvem (Google Gemini).

## 🆕 Novidades v1.4 (Testes Abrangentes + Correções)
- ✅ **🧪 Testes Abrangentes**: Suite completa de testes automatizados com 100% de sucesso
- ✅ **🔧 Correções HTTP 500**: Resolvidos todos os erros de listagem de modelos
- ✅ **📊 Validação Pydantic**: Schemas corrigidos para compatibilidade total
- ✅ **🌟 Google Gemini API**: Suporte completo à API Gemini do Google
- ✅ **🔀 Multi-Provider**: Alterne entre Ollama (local) e Gemini (nuvem)
- ✅ **🚀 Modelos Avançados**: Acesso aos modelos Gemini 2.0/2.5 mais recentes
- ✅ **📊 Lista Dinâmica**: Modelos sempre atualizados direto da API Google
- ✅ **🔑 Segurança**: Suporte a chaves API Gemini seguras
- ✅ **⚡ Performance**: Modelos em nuvem de alta performance
- ✅ **🛠️ Compatibilidade**: Mesma interface para ambos os provedores

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Endpoints](#-endpoints)
- [Provedores de IA](#-provedores-de-ia)
- [Teste](#-teste)
- [Escalabilidade](#-escalabilidade)
- [Segurança](#-segurança)
- [Monitoramento](#-monitoramento)
- [Troubleshooting](#-troubleshooting)

## 🚀 Características

- **🌟 Multi-Provider IA**: Suporte tanto para Ollama (local) quanto Google Gemini (nuvem)
- **🚀 Smart Upload**: Detecção automática de tipo de arquivo e ferramenta apropriada
- **⚙️ Configuração CPU/GPU**: Controle dinâmico do modo de processamento Ollama  
- **OCR Avançado**: Tesseract para extração de texto de imagens (JPG, PNG)
- **Parsers Múltiplos**: PDF, DOCX, XLSX com detecção automática
- **LLM Local & Nuvem**: Integração com Ollama (local) e Google Gemini (nuvem)
- **Gerenciamento de Modelos**: Download e listagem via API (ambos provedores)
- **Sistema de Filas**: Processamento assíncrono com Celery + Redis
- **Modo Verbose**: Logs detalhados mostrando detecção automática
- **Auto-Limpeza**: Remoção automática de arquivos e dados antigos
- **Containerizado**: Docker com todas as dependências
- **Escalável**: Suporte a paralelização baseada no hardware
- **Monitoramento**: Logs estruturados e health checks avançados

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Celery        │    │   Ollama        │
│   (API Server)  │────│   (Workers)     │────│   (Local LLM)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │   Google        │
         │                       └──────────────│   Gemini API    │
         │                                      │   (Cloud LLM)   │
         ▼                                      └─────────────────┘
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite        │    │   Redis         │    │   Tesseract     │
│   (Database)    │    │   (Queue)       │    │   (OCR)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Fluxo de Processamento

1. **Upload**: Cliente envia arquivo + headers obrigatórios (incluindo AI-Provider)
2. **Validação**: Verificação de API key, tipo e tamanho do arquivo, provider IA
3. **Fila de Extração**: Worker extrai texto (OCR/Parser)
4. **Fila de LLM**: Worker envia prompt para Ollama (local) ou Gemini (nuvem)
5. **Fila de Formatação**: Worker formata resposta final
6. **Resposta**: Cliente consulta resultado via API

## 🛠️ Instalação

### Pré-requisitos

- Docker 20.0+
- Docker Compose 2.0+
- 4GB+ RAM (recomendado 8GB+)
- 10GB+ espaço em disco
- **[OPCIONAL]** Chave API do Google Gemini (para usar modelos em nuvem)

### Instalação via Docker

1. **Clone o repositório**
```bash
git clone <repository-url>
cd MYELIN-OCR-LLM-LOCAL
```

2. **Configure o ambiente**
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

3. **Construa e execute o container**
```bash
# Opção 1: Docker Compose (recomendado)
docker-compose up --build

# Opção 2: Docker direto
docker build -t document-ocr-api .
docker run -p 8000:8000 -p 11434:11434 -v $(pwd)/uploads:/app/uploads document-ocr-api
```

4. **Aguarde a inicialização**
```bash
# Verificar se está funcionando
curl http://localhost:8000/health
```

**Tempo de inicialização**: ~5-10 minutos (download do modelo gemma3:1b)

## 🤖 Provedores de IA

### 🏠 Ollama (Local)
- **Vantagens**: Privacidade total, sem custos adicionais, funciona offline
- **Modelos**: gemma3:1b, qwen2:0.5b, llama3:8b, mistral:7b, etc.
- **Requisitos**: Hardware local com GPU/CPU adequados

### 🌟 Google Gemini (Nuvem)
- **Vantagens**: Modelos mais avançados, sem requisitos de hardware
- **Modelos**: gemini-2.0-flash, gemini-2.5-pro-preview, gemini-1.5-pro, etc.
- **Requisitos**: Chave API Gemini (gratuita com limites)

### Como Obter Chave API Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Faça login com sua conta Google
3. Clique em "Get API Key"
4. Copie sua chave API
5. Use no header `Gemini-API-Key` das requisições

## ⚙️ Configuração

### Arquivo .env

```bash
# API Configuration
API_KEY=myelin-ocr-llm-2024-super-secret-key
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=sqlite:///./documents.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Ollama Configuration (para uso local)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=gemma3:1b

# File Upload Configuration
MAX_FILE_SIZE=50
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,docx,xlsx,xls,doc

# Queue Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cleanup Configuration
CLEANUP_INTERVAL_HOURS=1
MAX_RECORD_AGE_HOURS=24

# Logging Configuration
LOG_LEVEL=INFO
LOG_ROTATION=10MB
```

## 📖 Como Usar

### 1. 🏠 Usando Ollama (Local)

```bash
# Processamento local com Ollama
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Verifique qual CNPJ existe nesse documento" \
  -H "Format-Response: [{\"CNPJ\": \"\"}]" \
  -H "Model: gemma3:1b" \
  -H "AI-Provider: ollama" \
  -F "file=@documento.pdf"
```

### 2. 🌟 Usando Google Gemini (Nuvem)

```bash
# Processamento em nuvem com Gemini
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Verifique qual CNPJ existe nesse documento e extraia todas as informações da empresa" \
  -H "Format-Response: [{\"Dia da Leitura\": \"\"}]" \
  -H "Model: gemini-2.0-flash" \
  -H "AI-Provider: gemini" \
  -H "Gemini-API-Key: SUA_CHAVE_API_GEMINI" \
  -H "Example: [{\"Dia da Leitura\": \"31/12/9999\"}]" \
  -F "file=@documento.pdf"
```

**🛠️ Detecção Automática:**
- `.jpg/.png` → Tesseract OCR
- `.pdf` → PyPDF2 Parser  
- `.docx` → python-docx Parser
- `.xlsx` → openpyxl Parser

**Resposta:**
```json
{
  "status": "success",
  "message": "Document uploaded and processing started",
  "document_id": 1,
  "filename": "documento.pdf",
  "ai_provider": "gemini",
  "model": "gemini-2.0-flash"
}
```

### 3. Verificar Status da Fila

```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/queue"
```

### 4. Obter Resposta

```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/response/1"
```

### 5. Gerenciamento de Modelos (NOVO!)

#### Listar Modelos Disponíveis
```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/models/list"
```

**Resposta:**
```json
{
  "status": "success",
  "models": [
    {"name": "gemma3:1b", "status": "available"},
    {"name": "llama3:8b", "status": "available"}
  ],
  "total_models": 2
}
```

#### Baixar Novo Modelo
```bash
curl -X POST "http://localhost:8000/models/download" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Model-Name: llama3:8b"
```

**🤖 Modelos Válidos e Recomendados:**
- **LLaMA 3 (Meta)**: `llama3:8b`, `llama3:70b`
- **Gemma 2 (Google)**: `gemma2:2b`, `gemma2:9b`, `gemma2:27b` 
- **Mistral AI**: `mistral:7b`, `mistral:instruct`
- **Qwen 2 (Alibaba)**: `qwen2:0.5b`, `qwen2:1.5b`, `qwen2:7b`
- **Phi-3 (Microsoft)**: `phi3:mini`, `phi3:medium`

💡 **Recomendações de uso:**
- `qwen2:0.5b` - Mais rápido (500MB)
- `gemma2:2b` - Equilibrado (1.6GB)  
- `llama3:8b` - Mais preciso (4.7GB)

⚠️ **Importante**: Download pode levar 5-30 minutos dependendo do modelo

### 6. ⚙️ Configuração CPU/GPU (NOVO!)

#### Verificar Modo Atual
```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/config/compute"
```

**Resposta:**
```json
{
  "status": "success",
  "compute_mode": "cpu",
  "gpu_enabled": false,
  "cuda_devices": "",
  "config": {
    "OLLAMA_COMPUTE_MODE": "cpu",
    "OLLAMA_GPU_ENABLED": "0",
    "CUDA_VISIBLE_DEVICES": ""
  }
}
```

#### Alternar para GPU (Mais Rápido)
```bash
curl -X POST "http://localhost:8000/config/compute" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Compute-Mode: gpu"
```

#### Alternar para CPU (Econômico)
```bash
curl -X POST "http://localhost:8000/config/compute" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Compute-Mode: cpu"
```

**🔄 Configuração Persistente:** As configurações são salvas no `.env` e aplicadas automaticamente.

### 7. Usando Modelos Diferentes

```bash
# Upload com LLaMA3:8b (mais preciso)
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Análise detalhada deste documento" \
  -H "Format-Response: [{\"análise\": \"\", \"detalhes\": \"\"}]" \
  -H "Model: llama3:8b" \
  -F "file=@documento.pdf"
```

## 🔗 Endpoints

| Método | Endpoint | Descrição | Headers Obrigatórios |
|--------|----------|-----------|---------------------|
| `POST` | `/upload` | 🚀 **SMART UPLOAD** - Auto-detecção | Key, Prompt, Format-Response, Model, AI-Provider |
| `GET` | `/queue` | Status da fila | Key |
| `GET` | `/response/{id}` | Resposta do documento | Key |
| `POST` | `/models/download` | Download de modelo Ollama | Key, Model-Name |
| `GET` | `/models/list` | Lista modelos Ollama | Key |
| `GET` | `/models/gemini` | **🌟 NOVO** - Lista modelos Gemini | Key, Gemini-API-Key |
| `POST` | `/config/compute` | **🆕 NOVO** - Configurar CPU/GPU | Key, Compute-Mode |
| `GET` | `/config/compute` | **🆕 NOVO** - Ver modo atual | Key |
| `GET` | `/health` | Health check | - |
| `GET` | `/` | Informações da API | - |

### Headers Obrigatórios

| Header | Exemplo | Descrição |
|--------|---------|-----------|
| `Key` | `myelin-ocr-llm-2024-super-secret-key` | Chave de autenticação |
| `Prompt` | `"Extraia o CNPJ"` | Pergunta sobre o documento |
| `Format-Response` | `[{"CNPJ": ""}]` | Formato esperado da resposta |
| `Model` | `gemma3:1b` ou `gemini-2.0-flash` | Modelo Ollama ou Gemini a usar |
| `Example` | `[{"CNPJ": "12.345.678/0001-90"}]` | Exemplo de resposta (opcional) |
| `AI-Provider` | `ollama` ou `gemini` | Provider de IA a usar |
| `Gemini-API-Key` | `AIzaSy...` | Chave API Gemini (obrigatória quando AI-Provider=gemini) |

### 🌟 Exemplos de Uso Gemini

#### Listar Modelos Gemini Disponíveis
```bash
curl -X GET "http://localhost:8000/models/gemini" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Gemini-API-Key: SUA_CHAVE_API_GEMINI"
```

**Resposta:**
```json
{
  "status": "success",
  "provider": "gemini",
  "models": [
    {
      "name": "gemini-2.0-flash",
      "display_name": "Gemini 2.0 Flash",
      "description": "Latest multimodal model with next generation features",
      "input_token_limit": "1,048,576",
      "output_token_limit": "8,192"
    },
    {
      "name": "gemini-2.5-pro-preview",
      "display_name": "Gemini 2.5 Pro Preview", 
      "description": "Most powerful thinking model with maximum accuracy",
      "input_token_limit": "1,048,576",
      "output_token_limit": "65,536"
    }
  ],
  "total_models": 7,
  "documentation": "https://ai.google.dev/gemini-api/docs/models"
}
```

#### Comparação de Modelos Recomendados

| Caso de Uso | Ollama (Local) | Gemini (Nuvem) | Vantagem |
|-------------|----------------|-----------------|----------|
| **Documentos Simples** | gemma3:1b | gemini-2.0-flash-lite | Local: Privacidade |
| **Análise Complexa** | llama3:8b | gemini-2.0-flash | Nuvem: Performance |
| **Raciocínio Avançado** | llama3:70b | gemini-2.5-pro-preview | Nuvem: Capacidade |
| **Alto Volume** | qwen2:0.5b | gemini-1.5-flash-8b | Local: Sem limite de requests |
| **Processamento Offline** | Qualquer | ❌ Não disponível | Local: Funcionamento offline |

### Status de Processamento

- `uploaded`: Arquivo recebido
- `text_extracted`: Texto extraído com sucesso
- `prompt_processed`: LLM processou o prompt

## 📚 Documentação Interativa (Swagger)

A API possui documentação interativa completa via Swagger/OpenAPI, permitindo testar todos os endpoints diretamente no navegador sem necessidade do Postman.

### 🌐 Acessando a Documentação

Com a aplicação rodando, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 🚀 Funcionalidades da Documentação

- **📋 Endpoints Organizados**: Agrupados por categorias com emojis
  - 📤 Upload de Documentos
  - 📊 Monitoramento  
  - 📄 Resultados
  - 🤖 Gestão de Modelos
  - ⚙️ Configuração
  - 🏥 Saúde
  - 🏠 Informações

- **🔧 Teste Interativo**: Execute requisições diretamente na interface
- **📖 Documentação Detalhada**: Descrições completas de parâmetros e respostas
- **🔐 Autenticação**: Interface para inserir chave API
- **📝 Exemplos**: Modelos de request/response para cada endpoint
- **🎯 Validação**: Validação automática de parâmetros

### 💡 Como Usar o Swagger

1. **Acesse**: http://localhost:8000/docs
2. **Autentique**: Clique em "Authorize" e insira sua API key
3. **Explore**: Navegue pelos endpoints organizados por categoria
4. **Teste**: Clique em "Try it out" para testar qualquer endpoint
5. **Execute**: Preencha os parâmetros e clique em "Execute"

### 🎯 Vantagens do Swagger

- ✅ **Sem Postman**: Teste direto no navegador
- ✅ **Documentação Sempre Atualizada**: Sincronizada automaticamente com o código
- ✅ **Interface Amigável**: Navegação intuitiva e organizada
- ✅ **Validação Automática**: Verifica parâmetros antes do envio
- ✅ **Exemplos Práticos**: Modelos de uso para cada endpoint
- ✅ **Suporte Completo**: Todos os endpoints documentados

### 📋 Exemplo de Teste via Swagger

1. Acesse http://localhost:8000/docs
2. Clique em "Authorize" e insira: `myelin-ocr-llm-2024-super-secret-key`
3. Expanda "📤 Upload de Documentos" → "POST /upload"
4. Clique em "Try it out"
5. Preencha os headers:
   - Prompt: `"Extraia o CNPJ deste documento"`
   - Format-Response: `[{"CNPJ": ""}]`
   - Model: `gemma3:1b`
   - AI-Provider: `ollama`
6. Faça upload de um arquivo
7. Clique em "Execute"
8. Veja a resposta em tempo real!

## 🧪 Teste

### 🎯 Suite de Testes Abrangentes (NOVO!)

**Status Atual: ✅ 100% de Sucesso (15/15 testes passando)**

Execute a suite completa de testes automatizados:

```bash
python comprehensive_api_test.py
```

**Cobertura de Testes:**
- ✅ **Status & Informações**: Health check e informações da API
- ✅ **Gestão de Modelos**: Listagem Ollama e Gemini (46+ modelos)
- ✅ **Smart Upload**: Upload multi-provider (Ollama + Gemini)
- ✅ **Monitoramento**: Status da fila com/sem debug
- ✅ **Resultados**: Recuperação de respostas com debug detalhado
- ✅ **Diagnósticos**: Debug completo de documentos
- ✅ **Configuração**: Gestão de modo CPU/GPU
- ✅ **Segurança**: Validação de chaves API e erros

**Exemplo de Saída:**
```
🧠 COMPREHENSIVE API TEST SUITE - Document OCR LLM API
================================================================================
📊 Total Tests: 15
✅ Passed: 15
❌ Failed: 0
📈 Success Rate: 100.0%
================================================================================
```

### Script de Teste Automatizado

```bash
# Windows
test_api.bat

# Linux/Mac
chmod +x test_api.sh
./test_api.sh
```

### Collection do Postman

1. **Importe os arquivos no Postman:**
   - `postman_collection.json` (Collection)
   - `postman_environment.json` (Environment)

2. **Configure o ambiente** "Document OCR LLM API - Local"

3. **Como usar:**
   - Execute "Health Check" primeiro
   - Execute "Upload Document (Image)" com arquivo `teste.jpg`
   - O `document_id` será preenchido automaticamente
   - Execute "Get Queue Status" para acompanhar
   - Execute "Get Document Response" para o resultado

### Testes Manuais

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Upload com teste.jpg
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Descreva o que você vê na imagem" \
  -H "Format-Response: {\"descricao\": \"\"}" \
  -H "Model: gemma3:1b" \
  -H "AI-Provider: ollama" \
  -F "file=@teste.jpg"

# 3. Verificar status
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  "http://localhost:8000/queue"
```

## 📈 Escalabilidade

### Configuração para Máquinas Modestas

```bash
# No .env
CELERY_WORKERS=1
CELERY_CONCURRENCY=1
MODEL=gemma3:1b
```

### Configuração para Máquinas Potentes

```bash
# No .env
CELERY_WORKERS=4
CELERY_CONCURRENCY=4
MODEL=llama2:7b
```

### Escalonamento Manual

```bash
# Adicionar mais workers
docker exec -d <container> celery -A workers worker --concurrency=4

# Monitorar workers
docker exec <container> celery -A workers inspect active
```

## 🔒 Segurança

### Validações Implementadas

- ✅ Autenticação via API Key
- ✅ Validação de tipos de arquivo
- ✅ Limitação de tamanho de arquivo
- ✅ Sanitização de inputs
- ✅ Rate limiting (via Celery)

### Configurações de Segurança

```bash
# Tipos de arquivo permitidos
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,docx,xlsx

# Tamanho máximo
MAX_FILE_SIZE=50

# API Key forte
API_KEY=myelin-ocr-llm-2024-super-secret-key
```

## 📊 Monitoramento (Modo Verbose Ativo!)

### Logs Detalhados em Tempo Real

O sistema agora opera em **modo verbose** com logs detalhados de todo o processo:

```bash
# Ver logs em tempo real do container
docker logs <container_name> -f

# Logs específicos por serviço (com modo verbose)
docker exec -it <container_name> tail -f /var/log/supervisor/fastapi.log     # FastAPI verbose
docker exec -it <container_name> tail -f /var/log/supervisor/celery_worker.log  # Celery debug
docker exec -it <container_name> tail -f /var/log/supervisor/ollama.log        # Ollama verbose

# Logs da aplicação (dentro do container)
docker exec -it <container_name> tail -f /app/logs/app.log        # Logs gerais
docker exec -it <container_name> tail -f /app/logs/verbose.log    # Logs verbose específicos
```

### 📋 O que você verá nos logs verbose:

#### 📤 **Smart Upload Process**
```
📤 VERBOSE: Starting document upload process
📁 VERBOSE: Filename: teste.jpg
🤖 VERBOSE: Model requested: gemma3:1b
📏 VERBOSE: File size: 2.45 MB
🔍 VERBOSE: Auto-detected file type: JPG
🛠️ VERBOSE: Will use extraction tool: Tesseract OCR
💾 VERBOSE: Saving file to disk...
✅ VERBOSE: File saved to: uploads/uuid_teste.jpg
🗄️ VERBOSE: Creating database record...
🚀 VERBOSE: Starting Celery task for document 123
```

#### 🔍 **OCR Process**
```
🔍 VERBOSE: Starting text extraction from JPG file: uploads/uuid_teste.jpg
🖼️ VERBOSE: Using OCR (Tesseract) for image processing
✅ VERBOSE: Text extraction completed. Extracted 847 characters
📄 VERBOSE: Text preview: NOTA FISCAL ELETRÔNICA...
```

#### 🤖 **LLM Process**
```
🤖 VERBOSE: Sending prompt to Ollama model 'gemma3:1b'
📄 VERBOSE: Context length: 847 characters
❓ VERBOSE: Prompt: Verifique qual CNPJ existe nesse documento
🔗 VERBOSE: Making request to http://localhost:11434/api/generate
✅ VERBOSE: Ollama response received (234 chars)
💬 VERBOSE: Response preview: O CNPJ encontrado no documento é...
⏱️ VERBOSE: Total duration: 3.45s
🔢 VERBOSE: Prompt tokens: 298
📊 VERBOSE: Response tokens: 87
```

#### ⚙️ **CPU/GPU Configuration**
```
🔄 VERBOSE: Switching Ollama compute mode to: GPU
🚀 VERBOSE: GPU mode enabled - CUDA devices accessible
🔄 VERBOSE: Restarting Ollama service with GPU mode...
✅ VERBOSE: Ollama restarted successfully in GPU mode
ℹ️ VERBOSE: Current compute mode: GPU
```

### Logs Tradicionais

### Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Ollama Health
curl http://localhost:11434/api/tags

# Redis Health
docker exec <container> redis-cli ping
```

### Métricas

```bash
# Status dos workers
docker exec <container> celery -A workers inspect stats

# Fila de tarefas
docker exec <container> celery -A workers inspect reserved

# Uso de recursos
docker stats <container_name>
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. 🚨 Status COMPLETED mas "Texto ainda não extraído"

**Sintoma**: Documento aparece como COMPLETED no `/queue` mas retorna "Texto ainda não extraído" no `/response/{id}`

**Causa**: Bug no pipeline de extração onde o texto não é salvo corretamente no banco de dados

**Soluções**:

1. **Diagnóstico Automático**:
```bash
# Use o endpoint de debug para diagnóstico completo
curl -X GET "http://localhost:8000/debug/document/1" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key"
```

2. **Script de Correção**:
```bash
# Execute o script de correção automática
python fix_extraction_bug.py
```

3. **Verificação Manual**:
```bash
# Verifique logs detalhados com debug=1
curl -X GET "http://localhost:8000/response/1" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "debug: 1"
```

4. **Rebuild Docker** (se necessário):
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. 🖼️ OCR não funciona (Tesseract)

**Sintomas**: Erro ao processar imagens JPG/PNG

**Soluções**:
```bash
# Verificar se Tesseract está instalado no container
docker exec -it <container_name> tesseract --version

# Reinstalar dependências se necessário
docker-compose build --no-cache
```

#### 3. 🤖 Ollama não responde (Erro 404)

**Sintomas**: Erro 404 ao acessar `http://localhost:11434/api/generate`

**Causa**: Ollama não está rodando ou não está configurado corretamente no container

**Soluções**:

1. **Verificação Rápida**:
```bash
# Usar script de verificação
./check_services.sh

# Ou testar manualmente
curl http://localhost:11434/api/tags
```

2. **Restart Simples**:
```bash
# Reiniciar apenas o container
docker-compose restart

# Aguardar 30-60 segundos e testar novamente
curl http://localhost:11434/api/tags
```

3. **Rebuild Completo**:
```bash
# Usar script automático
./rebuild_and_debug.sh

# Ou manualmente
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

4. **Verificar Logs do Ollama**:
```bash
# Ver logs específicos do Ollama
docker-compose logs document-ocr-api | grep -E "(ollama|Ollama)"

# Entrar no container para debug
docker exec -it $(docker-compose ps -q) bash
ollama serve --help
ps aux | grep ollama
```

5. **Usar Gemini como Alternativa**:
```bash
# Se Ollama falhar, use Gemini
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Extraia informações do documento" \
  -H "Format-Response: [{\"info\": \"\"}]" \
  -H "Model: gemini-2.0-flash" \
  -H "AI-Provider: gemini" \
  -H "Gemini-API-Key: SUA_CHAVE_API" \
  -F "file=@documento.pdf"
```

#### 4. 🌟 Gemini API não funciona

**Sintomas**: Erro 401 ou 403 com Gemini

**Soluções**:
- Verificar se a chave API está correta
- Verificar se há quota disponível
- Testar chave API diretamente:
```bash
curl -X GET "http://localhost:8000/models/gemini" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Gemini-API-Key: SUA_CHAVE_API"
```

#### 5. 📊 Redis/Celery não processa

**Sintomas**: Documentos ficam presos em UPLOADED

**Soluções**:
```bash
# Verificar Redis
docker-compose logs redis

# Verificar workers Celery
docker-compose logs worker

# Reiniciar workers
docker-compose restart worker
```

### Logs e Monitoramento

#### Logs Detalhados
```bash
# Ver logs em tempo real
docker-compose logs -f

# Logs específicos do worker
docker-compose logs -f worker

# Logs com timestamps
docker-compose logs -t
```

#### Health Checks
```bash
# Verificar saúde da aplicação
curl http://localhost:8000/health

# Verificar fila de processamento
curl -X GET "http://localhost:8000/queue" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key"
```

### Endpoints de Debug

#### 1. Debug de Documento Específico
```bash
GET /debug/document/{document_id}
```
Retorna diagnóstico completo incluindo:
- Status do arquivo no sistema
- Verificação de extração de texto
- Status do processamento LLM
- Inconsistências detectadas
- Teste de re-extração

#### 2. Debug de Response
```bash
GET /response/{document_id}
Header: debug=1
```
Retorna informações detalhadas:
- Conteúdo extraído pelo OCR/Parser
- Prompt completo enviado para LLM
- Resposta raw da LLM antes da formatação

### Script de Correção Automática

O arquivo `fix_extraction_bug.py` oferece:

1. **Verificação de Dependências**: Testa se todas as bibliotecas estão instaladas
2. **Diagnóstico de Banco**: Identifica documentos com problemas
3. **Teste de Extração**: Testa extração em arquivos reais
4. **Correção Automática**: Tenta corrigir documentos problemáticos

```bash
# Executar diagnóstico completo
python fix_extraction_bug.py

# Ou dentro do container Docker
docker exec -it <container_name> python fix_extraction_bug.py
```

### Prevenção de Problemas

1. **Monitoramento Regular**:
   - Use o endpoint `/queue` para verificar documentos presos
   - Configure alertas para documentos em processamento há muito tempo

2. **Backup Regular**:
   - Faça backup do banco `documents.db`
   - Mantenha logs para análise posterior

3. **Atualizações**:
   - Mantenha Docker e dependências atualizados
   - Teste em ambiente de desenvolvimento antes de produção

4. **Recursos Adequados**:
   - Monitore uso de CPU/RAM
   - Ajuste workers Celery conforme necessário

## 🚀 URLs Importantes

- **API Principal**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Ollama**: http://localhost:11434

## 📄 Arquivos de Configuração

- `build_and_run.bat` - Script de build para Windows
- `test_api.bat` - Script de teste para Windows
- `postman_collection.json` - Collection do Postman
- `postman_environment.json` - Environment do Postman
- `.env` - Configurações da aplicação
- `docker-compose.yml` - Orquestração de containers

## 📄 Licença

Este projeto está licenciado sob a **GNU Affero General Public License v3.0 (AGPL-3.0)**.

### 🆓 Uso Livre Permitido
- ✅ **Uso pessoal e educacional**
- ✅ **Pesquisa e desenvolvimento**
- ✅ **Projetos open source** (devem também usar licença compatível)
- ✅ **Contribuições** para este projeto

### 🏢 Uso Comercial
Para **uso comercial**, incluindo:
- 💼 Integração em produtos comerciais
- 🌐 Oferecimento como serviço (SaaS)
- 💰 Venda ou distribuição comercial
- 🏭 Uso em ambiente empresarial com fins lucrativos

**É necessária uma licença comercial separada.** Entre em contato:

📧 **Email**: carlosmagnosilvatavares@gmail.com  
💬 **LinkedIn**: https://www.linkedin.com/in/carlosmagnosilvatavares/
📄 **Termos**: Negociáveis conforme o caso de uso


### ⚖️ Compliance AGPL
Ao usar este software sob AGPL-3.0, você deve:
- 📖 **Manter avisos de copyright** em todos os arquivos
- 🔓 **Disponibilizar código fonte** de qualquer modificação
- 📋 **Usar licença compatível** em projetos derivados
- 🌐 **Fornecer código fonte** mesmo para uso como serviço web

### 📋 Licenças de Terceiros
Este projeto utiliza bibliotecas open source com suas respectivas licenças:
- **FastAPI**: MIT License
- **Tesseract OCR**: Apache 2.0 License  
- **Ollama**: MIT License
- **PostgreSQL**: PostgreSQL License
- **Redis**: BSD License

Para mais detalhes, consulte o arquivo [LICENSE](LICENSE).

### 🤝 Contribuições
Contribuições são bem-vindas! Ao contribuir, você concorda que suas contribuições serão licenciadas sob os mesmos termos deste projeto.

Para contribuir:
1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

🎯 **Pronto para usar!** O sistema está configurado para rodar em máquinas modestas e escalar conforme necessário.

📜 **Licenciado sob AGPL-3.0** - Uso livre para projetos compatíveis, licença comercial para uso empresarial.

---

**🧠 Powered by Myelin AI - Processamento inteligente de documentos**

## 🎯 **Sobre o Desenvolvimento deste Sistema**

### 📝 **Prompt-inicial-para-gerar-sistema-com-cursor-e-claude4.txt**

Este sistema foi **inteiramente gerado** através de engenharia de prompt avançada Criado pelo engenheiro de dados Carlos Magno utilizando **Claude Sonnet 4** no **Cursor IDE**. O arquivo `Prompt-inicial-para-gerar-sistema-com-cursor-e-claude4.txt` contém o prompt original e atualizado que foi usado para criar toda a aplicação.

#### 🔄 **Como Funciona:**

1. **📋 Prompt Inicial**: O arquivo contém especificações completas do sistema (Feito na Mão por um Humano)
1.2 **📋 Prompt Inicial Melhorado**: Foi feito com base no inicial, porém melhorado com GPT 4o
1.2.3 **📋 Prompt Inicial Melhorado Tecnicamente**: A parte técnica foi melhorada usando Claude 4 Thinking mode
2. **🤖 Claude Sonnet 4**: Interpreta e gera código baseado nas especificações
3. **⚡ Cursor IDE**: Facilita a implementação e refinamento do código
4. **🔧 Iterações**: Melhorias contínuas através de prompts refinados

#### 🏗️ **Arquitetura do Prompt:**

```
📝 Prompt Inicial v1.3
├── 🎯 Objetivo Principal
├── 📥 Requisitos Funcionais
│   ├── Headers obrigatórios
│   ├── Headers opcionais  
│   └── Multi-provider support
├── 🛠️ Requisitos Técnicos
│   ├── Infraestrutura Docker
│   ├── Sistema de filas
│   ├── Gerenciamento de modelos
│   └── Banco de dados
├── 📊 Endpoints Completos
│   ├── Core endpoints
│   ├── Gerenciamento de modelos
│   ├── Configuração avançada
│   └── Monitoramento
├── 🧪 Testes e Exemplos
├── 📁 Organização do projeto
├── 🛡️ Segurança
└── 🚀 Recursos avançados
```

#### 📈 **Evolução do Sistema:**

| Versão | Prompt Focus | Resultado |
|--------|--------------|-----------|
| **v1.0** | Sistema básico OCR + Ollama | Core functionality |
| **v1.1** | Smart upload + Auto-detection | File type detection |
| **v1.2** | CPU/GPU config + Model management | Performance optimization |
| **v1.3** | **Multi-provider AI + Gemini** | **Cloud + Local hybrid** |

#### 🎨 **Metodologia de Desenvolvimento:**

1. **📋 Especificação Detalhada**
   - Requisitos funcionais claros
   - Exemplos de uso concretos
   - Estrutura de arquivos definida

2. **🤖 Geração Assistida por IA**
   - Claude Sonnet 4 para lógica complexa
   - Cursor IDE para refinamentos
   - Iterações baseadas em feedback

3. **🔧 Refinamento Contínuo**
   - Testes em tempo real
   - Melhorias baseadas em uso
   - Documentação auto-atualizada

4. **📊 Validação Prática**
   - Collection Postman completa
   - Testes automatizados
   - Logs detalhados para debug

#### 💡 **Por que este Método é Eficaz:**

✅ **Especificação Completa**: O prompt detalha cada aspecto do sistema
✅ **Consistência Arquitetural**: Mantém padrões em todo o código
✅ **Documentação Automática**: README e collection gerados automaticamente
✅ **Testabilidade**: Inclui testes e validações desde o início
✅ **Escalabilidade**: Arquitetura pensada para crescimento
✅ **Manutenibilidade**: Código limpo e bem estruturado

#### 🔄 **Como Usar o Prompt:**

1. **📝 Para Recriar o Sistema:**
   ```bash
   # Cole o conteúdo do arquivo no Claude Sonnet 4
   # Especifique ajustes desejados
   # Execute no Cursor IDE
   ```

2. **🔧 Para Modificações:**
   ```bash
   # Edite seções específicas do prompt
   # Mantenha a estrutura geral
   # Atualize exemplos conforme necessário
   ```

3. **📈 Para Novas Funcionalidades:**
   ```bash
   # Adicione à seção "Recursos Avançados"
   # Especifique requisitos técnicos
   # Inclua exemplos de teste
   ```

#### 🎯 **Benefícios da Abordagem:**

| Vantagem | Descrição |
|----------|-----------|
| **⚡ Velocidade** | Sistema completo em horas, não semanas |
| **📊 Qualidade** | Padrões consistentes e best practices |
| **🔧 Flexibilidade** | Fácil modificação via prompt updates |
| **📚 Documentação** | Auto-gerada e sempre atualizada |
| **🧪 Testabilidade** | Testes incluídos desde o design |
| **🔄 Iteração** | Melhorias rápidas baseadas em feedback |

#### 🚀 **Futuro do Desenvolvimento:**

Esta metodologia representa o **futuro do desenvolvimento de software**:
- **🤖 IA como Copiloto Avançado**: Não apenas sugestões, mas arquitetura completa
- **📝 Especificação Declarativa**: Descrever "o que" ao invés de "como"
- **🔄 Iteração Rápida**: Mudanças arquiteturais em minutos
- **📊 Qualidade Consistente**: Padrões mantidos automaticamente

---

**💡 Dica**: Use este arquivo como template para seus próprios projetos. A engenharia de prompt bem feita pode acelerar drasticamente o desenvolvimento!

--- 

#### Pode usar mas poh pelo menos me da o crédito, deu trabalho fazer isso aqui, olha os commits foram madrugadas a dentro para criar esse sistema.

### 🔧 Teste Interativo
- **Interface Swagger**: Teste todos os endpoints diretamente no navegador
- **Validação de Headers**: Campos obrigatórios claramente identificados
- **Exemplos de Resposta**: Visualize o formato esperado de cada endpoint
- **Códigos de Status**: Documentação completa de erros e sucessos

### 🐛 **Modo Debug Avançado**

O endpoint `/response/{document_id}` possui um modo debug especial para análise detalhada:

#### 🔍 **Ativação do Debug**
```bash
# Header obrigatório para ativar debug
debug: 1
```

#### 📊 **Informações Retornadas no Debug**

1. **🔤 Conteúdo Extraído (OCR/Parser)**
   - Texto completo extraído do documento
   - Ferramenta de extração utilizada (Tesseract, PyPDF2, etc.)
   - Informações do arquivo (nome, tipo, tamanho)
   - Estatísticas de caracteres extraídos

2. **🤖 Prompt Enviado para LLM**
   - Prompt original do usuário
   - Prompt completo construído (com contexto e instruções)
   - Configurações de formatação solicitadas
   - Exemplos fornecidos
   - Provedor de AI utilizado (Ollama/Gemini)

3. **💬 Resposta Raw da LLM**
   - Resposta bruta/original da LLM
   - Resposta final formatada
   - Estatísticas de tokens/caracteres
   - Comparação antes/depois da formatação

#### 🎯 **Uso Prático do Debug**
- **Qualidade OCR**: Verificar se o texto foi extraído corretamente
- **Prompt Engineering**: Analisar se o prompt está bem construído
- **Troubleshooting**: Identificar onde está o problema (extração, prompt ou modelo)
- **Otimização**: Melhorar prompts baseado na resposta raw

## 🔗 Endpoints da API