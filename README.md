# 🧠 Document OCR LLM API

API escalável, segura e leve para análise de documentos com auxílio de modelos de linguagem locais (Ollama).

## 🆕 Novidades v1.2 (Smart Upload & Configuração Avançada)
- ✅ **🚀 SMART UPLOAD**: Detecção automática de tipo de arquivo e ferramenta
- ✅ **⚙️ Configuração CPU/GPU**: Alterne entre CPU e GPU para Ollama
- ✅ **🔄 Persistência**: Configurações salvas automaticamente
- ✅ **📊 Logs Verbosos**: Mostra detecção automática e modo de processamento
- ✅ **🤖 Gerenciamento de Modelos**: Download e listagem via API
- ✅ **🛠️ Auto-detecção**: JPG→OCR, PDF→Parser, DOCX→Parser, etc. 

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Endpoints](#-endpoints)
- [Teste](#-teste)
- [Escalabilidade](#-escalabilidade)
- [Segurança](#-segurança)
- [Monitoramento](#-monitoramento)
- [Troubleshooting](#-troubleshooting)

## 🚀 Características

- **🚀 Smart Upload**: Detecção automática de tipo de arquivo e ferramenta apropriada
- **⚙️ Configuração CPU/GPU**: Controle dinâmico do modo de processamento Ollama  
- **OCR Avançado**: Tesseract para extração de texto de imagens (JPG, PNG)
- **Parsers Múltiplos**: PDF, DOCX, XLSX com detecção automática
- **LLM Local**: Integração com Ollama (qualquer modelo suportado)
- **Gerenciamento de Modelos**: Download e listagem via API
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
│   (API Server)  │────│   (Workers)     │────│   (LLM)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite        │    │   Redis         │    │   Tesseract     │
│   (Database)    │    │   (Queue)       │    │   (OCR)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Fluxo de Processamento

1. **Upload**: Cliente envia arquivo + headers obrigatórios
2. **Validação**: Verificação de API key, tipo e tamanho do arquivo
3. **Fila de Extração**: Worker extrai texto (OCR/Parser)
4. **Fila de LLM**: Worker envia prompt para Ollama
5. **Fila de Formatação**: Worker formata resposta final
6. **Resposta**: Cliente consulta resultado via API

## 🛠️ Instalação

### Pré-requisitos

- Docker 20.0+
- Docker Compose 2.0+
- 4GB+ RAM (recomendado 8GB+)
- 10GB+ espaço em disco

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

# Ollama Configuration
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

### Modificar Modelo Ollama

```bash
# Entrar no container
docker exec -it <container_name> bash

# Listar modelos disponíveis
ollama list

# Instalar novo modelo
ollama pull llama2:7b

# Atualizar .env
# DEFAULT_MODEL=llama2:7b
```

## 📖 Como Usar

### 1. 🚀 Smart Upload (Detecção Automática)

```bash
# O sistema detecta automaticamente que é uma imagem e usa OCR
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Verifique qual CNPJ existe nesse documento" \
  -H "Format-Response: [{\"CNPJ\": \"\"}]" \
  -H "Model: gemma3:1b" \
  -F "file=@teste.jpg"

# Para PDF - detecta automaticamente e usa parser PDF
curl -X POST "http://localhost:8000/upload" \
  -H "Key: myelin-ocr-llm-2024-super-secret-key" \
  -H "Prompt: Extraia dados pessoais deste documento" \
  -H "Format-Response: [{\"nome\": \"\", \"cpf\": \"\"}]" \
  -H "Model: gemma3:1b" \
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
  "filename": "teste.jpg"
}
```

### 2. Verificar Status da Fila

```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/queue"
```

### 3. Obter Resposta

```bash
curl -H "Key: myelin-ocr-llm-2024-super-secret-key" "http://localhost:8000/response/1"
```

### 4. Gerenciamento de Modelos (NOVO!)

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

### 5. ⚙️ Configuração CPU/GPU (NOVO!)

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

### 6. Usando Modelos Diferentes

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
| `POST` | `/upload` | 🚀 **SMART UPLOAD** - Auto-detecção | Key, Prompt, Format-Response, Model |
| `GET` | `/queue` | Status da fila | Key |
| `GET` | `/response/{id}` | Resposta do documento | Key |
| `POST` | `/models/download` | Download de modelo | Key, Model-Name |
| `GET` | `/models/list` | Lista modelos | Key |
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
| `Model` | `gemma3:1b` | Modelo Ollama a usar |
| `Example` | `[{"CNPJ": "12.345.678/0001-90"}]` | Exemplo de resposta (opcional) |

### Status de Processamento

- `uploaded`: Arquivo recebido
- `text_extracted`: Texto extraído com sucesso
- `prompt_processed`: LLM processou o prompt
- `completed`: Processamento finalizado
- `error`: Erro durante processamento

## 🧪 Teste

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

#### 1. Container não inicia
```bash
# Verificar logs
docker logs <container_name>

# Verificar portas
netstat -tulpn | grep :8000
```

#### 2. Ollama não responde
```bash
# Verificar se o modelo foi baixado
docker exec <container> ollama list

# Baixar modelo manualmente
docker exec <container> ollama pull gemma3:1b
```

#### 3. Workers não processam
```bash
# Verificar Redis
docker exec <container> redis-cli ping

# Reiniciar workers
docker exec <container> supervisorctl restart celery_worker
```

#### 4. Erro de OCR
```bash
# Verificar Tesseract
docker exec <container> tesseract --version

# Testar OCR
docker exec <container> tesseract /app/teste.jpg stdout -l por
```

### Limpeza Manual

```bash
# Limpar arquivos antigos
docker exec <container> python3 -c "from utils import cleanup_old_files; cleanup_old_files()"

# Limpar banco de dados
docker exec <container> python3 -c "
from database import SessionLocal
from models import Document
from datetime import datetime, timedelta
db = SessionLocal()
cutoff = datetime.utcnow() - timedelta(hours=1)
deleted = db.query(Document).filter(Document.created_at < cutoff).delete()
db.commit()
print(f'Deleted {deleted} records')
"
```

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

📧 **Email**: license@myelin-ai.com  
💬 **LinkedIn**: [Seu Perfil LinkedIn]  
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