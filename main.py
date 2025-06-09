from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Depends, status, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from database import get_async_db, init_database, close_database, SessionLocal
from models import Document, DocumentStatus
from utils import is_allowed_file, save_uploaded_file, validate_file_size, list_gemini_models
from workers import extract_text_task
from loguru import logger
from dotenv import load_dotenv
import os
from typing import Optional, List
import uvicorn

load_dotenv()

# Initialize logging in verbose mode
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="DEBUG")
logger.add("logs/verbose.log", rotation="5 MB", retention="3 days", level="DEBUG")
logger.info("🚀 VERBOSE MODE ENABLED - Detailed logging activated")

# Create FastAPI app with enhanced Swagger documentation
app = FastAPI(
    title="Document OCR LLM API",
    description="""
    # 🚀 API para Análise de Documentos com OCR e LLM Local
    
    Esta API permite upload e análise inteligente de documentos usando OCR (Optical Character Recognition) 
    combinado com modelos de linguagem local (LLM) via Ollama ou Google Gemini.
    
    ## 🔧 Funcionalidades Principais:
    
    - **Upload Inteligente**: Detecção automática do tipo de arquivo e ferramenta de extração apropriada
    - **OCR Multi-formato**: Suporte para imagens (JPG, PNG), PDFs, Word (DOCX), Excel (XLSX)
    - **AI Providers**: Ollama (local) ou Google Gemini (cloud)
    - **Análise Personalizada**: Prompts customizados para análise específica do documento
    - **Processamento Assíncrono**: Queue system com Celery para processamento em background
    - **Monitoramento**: Health checks e status de processamento
    
    ## 🔐 Autenticação:
    
    Todos os endpoints (exceto `/health` e `/`) requerem autenticação via header `Key`.
    
    ## 🤖 Modelos Suportados:
    
    - **Ollama**: gemma3:1b, qwen2:0.5b, llama3, etc.
    - **Gemini**: gemini-2.0-flash, gemini-1.5-pro, etc.
    
    ## 📋 Fluxo de Trabalho:
    
    1. Upload do documento via `/upload`
    2. Monitoramento do status via `/queue` 
    3. Recuperação do resultado via `/response/{document_id}`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Document OCR LLM API",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configuration
API_KEY = os.getenv("API_KEY", "your-super-secret-api-key-here")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Pydantic models for API documentation
class UploadResponse(BaseModel):
    """Resposta do upload de documento"""
    status: str = Field(description="Status da operação")
    message: str = Field(description="Mensagem descritiva")
    document_id: int = Field(description="ID único do documento")
    filename: str = Field(description="Nome do arquivo enviado")
    ai_provider: str = Field(description="Provedor de AI utilizado (ollama/gemini)")
    extraction_tool: str = Field(description="Ferramenta de extração utilizada")
    file_type: str = Field(description="Tipo do arquivo detectado")

class DocumentResponse(BaseModel):
    """Resposta com resultado da análise do documento"""
    status: str = Field(description="Status da operação")
    data: dict = Field(description="Dados do documento e resultado")

class DocumentDebugResponse(BaseModel):
    """Resposta completa com informações de debug"""
    status: str = Field(description="Status da operação")
    data: dict = Field(description="Dados do documento e resultado")
    debug_info: Optional[dict] = Field(description="Informações de debug (apenas quando debug=1)", default=None)

class QueueStatus(BaseModel):
    """Status da fila de processamento"""
    status: str = Field(description="Status da operação")
    total_documents: int = Field(description="Número total de documentos")
    queue: List[dict] = Field(description="Lista de documentos na fila")

class HealthCheck(BaseModel):
    """Status de saúde da aplicação"""
    status: str = Field(description="Status geral da aplicação")
    message: str = Field(description="Mensagem descritiva")

class ModelInfo(BaseModel):
    """Informações sobre um modelo"""
    name: str = Field(description="Nome do modelo")
    size: Optional[str] = Field(description="Tamanho do modelo")
    modified: Optional[str] = Field(description="Data de modificação")
    status: Optional[str] = Field(description="Status do modelo")

class ModelsListResponse(BaseModel):
    """Lista de modelos disponíveis"""
    status: str = Field(description="Status da operação")
    provider: str = Field(description="Provedor dos modelos")
    models: List[ModelInfo] = Field(description="Lista de modelos disponíveis")

class ComputeConfig(BaseModel):
    """Configuração de modo computacional"""
    compute_mode: str = Field(description="Modo computacional (CPU/GPU)")
    
class ComputeConfigResponse(BaseModel):
    """Resposta da configuração computacional"""
    status: str = Field(description="Status da operação")
    compute_mode: str = Field(description="Modo computacional atual")
    message: str = Field(description="Mensagem descritiva")

class ErrorResponse(BaseModel):
    """Resposta de erro padrão"""
    detail: str = Field(description="Descrição do erro")

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("Application started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_database()
    logger.info("Application shutdown successfully")

# Dependency for API key validation
def validate_api_key(key: str = Header(..., alias="Key")):
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return key

# Helper function for debug info
def get_extraction_tool_name(file_type: str) -> str:
    """Get the extraction tool name based on file type"""
    if file_type.lower() in ['jpg', 'jpeg', 'png']:
        return "Tesseract OCR"
    elif file_type.lower() == 'pdf':
        return "PyPDF2 Parser"
    elif file_type.lower() in ['docx', 'doc']:
        return "python-docx Parser"
    elif file_type.lower() in ['xlsx', 'xls']:
        return "openpyxl Parser"
    else:
        return "Unknown Parser"

@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["📤 Upload de Documentos"],
    summary="Upload e análise inteligente de documentos",
    description="Faz upload de um documento e inicia o processamento com OCR + LLM",
    responses={
        200: {"description": "Upload realizado com sucesso", "model": UploadResponse},
        400: {"description": "Erro de validação", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Arquivo para upload (JPG, PNG, PDF, DOCX, XLSX)"),
    prompt: str = Header(..., alias="Prompt", description="Pergunta/prompt para análise do documento"),
    format_response: str = Header(..., alias="Format-Response", description="Formato esperado da resposta (ex: JSON, texto)"),
    model: str = Header(..., alias="Model", description="Modelo a usar (ex: gemma3:1b para Ollama, gemini-2.0-flash para Gemini)"),
    example: Optional[str] = Header(None, alias="Example", description="Exemplo opcional do formato de resposta esperado"),
    ai_provider: Optional[str] = Header("ollama", alias="AI-Provider", description="Provedor de AI: 'ollama' (padrão) ou 'gemini'"),

    key: str = Depends(validate_api_key)
):
    """
    🚀 SMART UPLOAD - Automatically detects file type and uses appropriate extraction tool
    
    Headers required:
    - Key: API authentication key
    - Prompt: Question to ask about the document
    - Format-Response: Expected response format (e.g., JSON)
    - Model: Model to use (e.g., gemma3:1b for Ollama, gemini-2.0-flash for Gemini)
    - Example: Optional example of expected response format
    - AI-Provider: "ollama" (default) or "gemini"
    - GEMINI_API_KEY: Required in .env when AI-Provider is "gemini"
    
    📋 Supported file types with automatic detection:
    - Images (JPG, JPEG, PNG) → Tesseract OCR
    - PDFs → PyPDF2 Parser  
    - Word docs (DOCX, DOC) → python-docx Parser
    - Excel files (XLSX, XLS) → openpyxl Parser
    
    🤖 Supported AI Providers:
    - Ollama (Local): Use local models like gemma3:1b, qwen2:0.5b, etc.
    - Google Gemini: Use cloud models like gemini-2.0-flash, gemini-1.5-pro, etc.
    
    🤖 The system automatically:
    1. Detects file extension
    2. Uses appropriate extraction tool
    3. Processes with selected AI provider and model
    4. Returns formatted response
    """
    try:
        logger.info(f"📤 VERBOSE: Starting document upload process")
        logger.info(f"📁 VERBOSE: Filename: {file.filename}")
        logger.info(f"🤖 VERBOSE: AI Provider: {ai_provider}")
        logger.info(f"🤖 VERBOSE: Model requested: {model}")
        logger.info(f"❓ VERBOSE: Prompt: {prompt}")
        
        # Validate AI provider
        if ai_provider not in ["ollama", "gemini"]:
            logger.error(f"❌ VERBOSE: Invalid AI provider: {ai_provider}")
            raise HTTPException(
                status_code=400, 
                detail="AI-Provider must be either 'ollama' or 'gemini'"
            )
        
        # Validate Gemini API key when using Gemini
        if ai_provider == "gemini" and not GEMINI_API_KEY:
            logger.error(f"❌ VERBOSE: Gemini API key required when using Gemini provider")
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY not configured in environment when AI-Provider is 'gemini'"
            )
        
        # Validate file
        if not file.filename:
            logger.error(f"❌ VERBOSE: No filename provided")
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not is_allowed_file(file.filename):
            logger.error(f"❌ VERBOSE: File type not allowed: {file.filename}")
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Supported types: {os.getenv('ALLOWED_EXTENSIONS')}"
            )
        
        # Read file content
        logger.info(f"📖 VERBOSE: Reading file content...")
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        logger.info(f"📏 VERBOSE: File size: {file_size_mb:.2f} MB")
        
        # Validate file size
        if not validate_file_size(len(file_content)):
            max_size_mb = int(os.getenv("MAX_FILE_SIZE", "50"))
            logger.error(f"❌ VERBOSE: File too large: {file_size_mb:.2f}MB > {max_size_mb}MB")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )
        
        # Save file and detect type
        logger.info(f"💾 VERBOSE: Saving file to disk...")
        file_path = save_uploaded_file(file_content, file.filename)
        file_type = file.filename.rsplit('.', 1)[1].lower()
        logger.info(f"✅ VERBOSE: File saved to: {file_path}")
        logger.info(f"🔍 VERBOSE: Auto-detected file type: {file_type.upper()}")
        
        # Log which extraction tool will be used
        extraction_tool = "Unknown"
        if file_type in ['jpg', 'jpeg', 'png']:
            extraction_tool = "Tesseract OCR"
        elif file_type == 'pdf':
            extraction_tool = "PyPDF2 Parser"
        elif file_type in ['docx', 'doc']:
            extraction_tool = "python-docx Parser"
        elif file_type in ['xlsx', 'xls']:
            extraction_tool = "openpyxl Parser"
        
        logger.info(f"🛠️ VERBOSE: Will use extraction tool: {extraction_tool}")
        
        # Get database connection
        database = await get_async_db()
        
        # Create document record using SQLAlchemy ORM for consistency
        logger.info(f"🗄️ VERBOSE: Creating database record...")
        from sqlalchemy.orm import Session
        db = SessionLocal()
        try:
            document = Document(
                filename=file.filename,
                file_type=file_type,
                file_path=file_path,
                prompt=prompt,
                format_response=format_response,
                example=example,
                model=model,
                ai_provider=ai_provider,
                gemini_api_key=GEMINI_API_KEY if ai_provider == "gemini" else None,
                status=DocumentStatus.UPLOADED
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            document_id = document.id
            logger.info(f"✅ VERBOSE: Document record created with ID: {document_id}")
        finally:
            db.close()
        
        # Start processing chain
        logger.info(f"🚀 VERBOSE: Starting Celery task for document {document_id}")
        extract_text_task.delay(document_id)
        
        logger.info(f"🎉 VERBOSE: Document uploaded successfully: {document_id}")
        
        return UploadResponse(
            status="success",
            message="Document uploaded and processing started",
            document_id=document_id,
            filename=file.filename,
            ai_provider=ai_provider,
            extraction_tool=extraction_tool,
            file_type=file_type.upper()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/queue",
    response_model=QueueStatus,
    tags=["📊 Monitoramento"],
    summary="Status da fila de processamento",
    description="Retorna o status de todos os documentos na fila de processamento",
    responses={
        200: {"description": "Status da fila obtido com sucesso", "model": QueueStatus},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def get_queue_status(
    key: str = Depends(validate_api_key)
):
    """
    Get status of all documents in the processing queue
    """
    try:
        # Get database connection
        database = await get_async_db()
        
        # Get all documents with their status
        query = """
        SELECT id, filename, status, created_at, updated_at, completed_at, error_message
        FROM documents 
        ORDER BY created_at DESC
        """
        
        documents = await database.fetch_all(query)
        
        queue_status = []
        for doc in documents:
            status_info = {
                "document_id": doc["id"],
                "filename": doc["filename"],
                "status": doc["status"],
                "created_at": doc["created_at"],
                "updated_at": doc["updated_at"],
                "completed_at": doc["completed_at"]
            }
            
            if doc["error_message"]:
                status_info["error_message"] = doc["error_message"]
                
            queue_status.append(status_info)
        
        return {
            "status": "success",
            "total_documents": len(queue_status),
            "queue": queue_status
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/response/{document_id}",
    response_model=DocumentDebugResponse,
    tags=["📄 Resultados"],
    summary="Obter resultado da análise do documento",
    description="Retorna o resultado da análise para um documento específico. Use header 'debug=1' para informações detalhadas de debug",
    responses={
        200: {"description": "Resultado obtido com sucesso", "model": DocumentDebugResponse},
        404: {"description": "Documento não encontrado", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def get_document_response(
    document_id: int = Path(..., description="ID do documento"),
    debug: Optional[str] = Header(None, alias="debug", description="Modo debug: '1' para informações detalhadas, '0' ou ausente para resposta normal"),
    key: str = Depends(validate_api_key)
):
    """
    Get the response for a specific document
    """
    try:
        # Get database connection
        database = await get_async_db()
        
        # Get document from database
        query = """
        SELECT id, filename, status, created_at, completed_at, formatted_response, llm_response, error_message,
               model, ai_provider, gemini_api_key, file_type, file_path, prompt, format_response, example,
               extracted_text, full_prompt_sent
        FROM documents 
        WHERE id = :document_id
        """
        
        document = await database.fetch_one(query, {"document_id": document_id})
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        response_data = {
            "document_id": document["id"],
            "filename": document["filename"],
            "status": document["status"],
            "created_at": document["created_at"],
            "completed_at": document["completed_at"]
        }
        
        # Handle both enum and string status formats
        doc_status = document["status"]
        if doc_status in [DocumentStatus.COMPLETED.value, "COMPLETED", DocumentStatus.COMPLETED]:
            # VERIFICAÇÃO CRÍTICA: Detectar inconsistência entre status e conteúdo
            extracted_text = document["extracted_text"] or ""
            if not extracted_text.strip() or extracted_text == "Texto ainda não extraído":
                logger.error(f"❌ CRITICAL INCONSISTENCY: Document {document_id} has status COMPLETED but no extracted text!")
                logger.error(f"❌ CRITICAL: extracted_text: '{extracted_text}'")
                logger.error(f"❌ CRITICAL: This indicates a serious bug in the extraction pipeline")
                
                # Adicionar aviso na resposta
                response_data["response"] = document["formatted_response"]
                response_data["llm_response"] = document["llm_response"]
                response_data["warning"] = "INCONSISTÊNCIA DETECTADA: Status COMPLETED mas texto não foi extraído corretamente"
            else:
                response_data["response"] = document["formatted_response"]
                response_data["llm_response"] = document["llm_response"]
        elif doc_status in [DocumentStatus.ERROR.value, "ERROR", DocumentStatus.ERROR]:
            response_data["error_message"] = document["error_message"]
        else:
            response_data["message"] = "Document is still being processed"
        
        # Adicionar informações de debug se solicitado
        debug_info = None
        if debug == "1":
            debug_info = {
                "1_extracted_content": {
                    "description": "Texto extraído do documento pelo OCR/Parser",
                    "extraction_tool": get_extraction_tool_name(document["file_type"]),
                    "content": document["extracted_text"] or "Texto ainda não extraído",
                    "content_length": len(document["extracted_text"]) if document["extracted_text"] else 0,
                    "file_info": {
                        "filename": document["filename"],
                        "file_type": document["file_type"],
                        "file_path": document["file_path"]
                    }
                },
                "2_prompt_sent_to_llm": {
                    "description": "Prompt completo enviado para a LLM (incluindo contexto, instruções e formatação)",
                    "ai_provider": document["ai_provider"],
                    "model": document["model"],
                    "original_prompt": document["prompt"],
                    "format_requested": document["format_response"],
                    "example_provided": document["example"],
                    "full_prompt_sent": document["full_prompt_sent"] or "Prompt ainda não enviado",
                    "prompt_length": len(document["full_prompt_sent"]) if document["full_prompt_sent"] else 0
                },
                "3_raw_llm_response": {
                    "description": "Resposta raw/bruta da LLM antes da formatação",
                    "raw_response": document["llm_response"] or "Resposta ainda não recebida",
                    "response_length": len(document["llm_response"]) if document["llm_response"] else 0,
                    "final_formatted_response": document["formatted_response"] or "Resposta ainda não formatada"
                }
            }
        
        return DocumentDebugResponse(
            status="success",
            data=response_data,
            debug_info=debug_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["🏥 Saúde"],
    summary="Verificação de saúde da aplicação",
    description="Endpoint para verificar se a aplicação está funcionando corretamente",
    responses={
        200: {"description": "Aplicação funcionando corretamente", "model": HealthCheck},
    }
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Document OCR LLM API is running"
    }

@app.post(
    "/models/download",
    tags=["🤖 Gestão de Modelos"],
    summary="Download de modelo Ollama",
    description="Faz download de um novo modelo Ollama",
    responses={
        200: {"description": "Modelo baixado com sucesso"},
        400: {"description": "Erro de validação", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def download_model(
    model_name: str = Header(..., alias="Model-Name", description="Nome do modelo para download (ex: llama3:8b, gemma2:2b)"),
    key: str = Depends(validate_api_key)
):
    """
    Download a new Ollama model
    
    Headers required:
    - Key: API authentication key
    - Model-Name: Name of the model to download
    
    🤖 Valid model examples:
    - "llama3:8b", "llama3:70b" (Meta LLaMA 3)
    - "gemma2:2b", "gemma2:9b", "gemma2:27b" (Google Gemma 2) 
    - "mistral:7b", "mistral:instruct" (Mistral AI)
    - "qwen2:0.5b", "qwen2:1.5b", "qwen2:7b" (Alibaba Qwen 2)
    - "phi3:mini", "phi3:medium" (Microsoft Phi-3)
    
    ⚠️ Note: Download time varies by model size (2-30 minutes)
    """
    try:
        import subprocess
        import asyncio
        
        logger.info(f"Starting download of model: {model_name}")
        
        # Create async process to download model
        process = await asyncio.create_subprocess_exec(
            'ollama', 'pull', model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd='/app'
        )
        
        # Wait for completion with timeout (10 minutes)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            
            # Decode outputs
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            logger.info(f"🔄 VERBOSE: Ollama pull completed with return code: {process.returncode}")
            logger.info(f"📤 VERBOSE: Stdout: {stdout_text}")
            logger.info(f"📥 VERBOSE: Stderr: {stderr_text}")
            
            if process.returncode == 0:
                # Double-check if model was actually downloaded by listing models
                import time
                time.sleep(2)  # Wait for model to be registered
                
                try:
                    # Verify model is actually available
                    verify_result = subprocess.run(
                        ['ollama', 'list'],
                        capture_output=True,
                        text=True,
                        cwd='/app'
                    )
                    
                    if verify_result.returncode == 0:
                        # Check if our model is in the list
                        models_output = verify_result.stdout
                        model_found = model_name in models_output
                        
                        if model_found:
                            logger.info(f"✅ VERBOSE: Model {model_name} downloaded and verified successfully")
                            return {
                                "status": "success",
                                "message": f"Model {model_name} downloaded successfully",
                                "model_name": model_name,
                                "output": stdout_text
                            }
                        else:
                            # Model download reported success but model not found in list
                            error_msg = f"Model '{model_name}' download completed but model not found in Ollama registry. This model may not exist or may have been corrupted."
                            logger.error(f"❌ VERBOSE: {error_msg}")
                            raise HTTPException(
                                status_code=404,
                                detail=error_msg
                            )
                    else:
                        # Could not verify, but process was successful
                        logger.warning(f"⚠️ VERBOSE: Could not verify model {model_name} but download process completed")
                        return {
                            "status": "success",
                            "message": f"Model {model_name} download completed (verification unavailable)",
                            "model_name": model_name,
                            "output": stdout_text
                        }
                        
                except Exception as verify_error:
                    # Could not verify, but process was successful
                    logger.warning(f"⚠️ VERBOSE: Could not verify model {model_name}: {verify_error}")
                    return {
                        "status": "success", 
                        "message": f"Model {model_name} download completed (verification failed)",
                        "model_name": model_name,
                        "output": stdout_text
                    }
            else:
                # Improved error handling with specific messages
                if "file does not exist" in stderr_text:
                    error_msg = f"Model '{model_name}' does not exist. Please check the model name and try again."
                    logger.error(f"❌ VERBOSE: {error_msg}")
                    raise HTTPException(
                        status_code=404,
                        detail=error_msg
                    )
                elif "connection" in stderr_text.lower():
                    error_msg = f"Network error downloading model '{model_name}'. Please check your internet connection."
                    logger.error(f"❌ VERBOSE: {error_msg}")
                    raise HTTPException(
                        status_code=503,
                        detail=error_msg
                    )
                else:
                    error_msg = f"Failed to download model '{model_name}': {stderr_text}"
                    logger.error(f"❌ VERBOSE: {error_msg}")
                    raise HTTPException(
                        status_code=400,
                        detail=error_msg
                    )
                
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            error_msg = f"Model download timed out after 10 minutes for '{model_name}'"
            logger.error(f"⏰ VERBOSE: {error_msg}")
            raise HTTPException(
                status_code=408,
                detail=error_msg
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Unexpected error downloading model '{model_name}': {str(e)}"
        logger.error(f"💥 VERBOSE: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get(
    "/models/list",
    response_model=ModelsListResponse,
    tags=["🤖 Gestão de Modelos"],
    summary="Listar modelos Ollama disponíveis",
    description="Retorna lista de todos os modelos Ollama instalados localmente",
    responses={
        200: {"description": "Lista de modelos obtida com sucesso", "model": ModelsListResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def list_models(
    key: str = Depends(validate_api_key)
):
    """
    List all available Ollama models
    """
    try:
        import subprocess
        import json
        
        logger.info("Listing available models")
        
        # Get list of models
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        
        if result.returncode == 0:
            models_output = result.stdout.strip()
            
            # Parse the output to extract model names
            models = []
            lines = models_output.split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        model_name = parts[0]
                        model_size = parts[1] if len(parts) > 1 else None
                        model_modified = parts[2] + " " + parts[3] if len(parts) > 3 else None
                        
                        models.append({
                            "name": model_name,
                            "size": model_size,
                            "modified": model_modified,
                            "status": "available"
                        })
            
            return {
                "status": "success",
                "provider": "ollama",
                "models": models
            }
        else:
            logger.error(f"Failed to list models: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list models: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@app.post(
    "/config/compute",
    response_model=ComputeConfigResponse,
    tags=["⚙️ Configuração"],
    summary="Definir modo computacional",
    description="Define o modo computacional para processamento (CPU ou GPU)",
    responses={
        200: {"description": "Configuração alterada com sucesso", "model": ComputeConfigResponse},
        400: {"description": "Erro de validação", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def set_compute_mode(
    compute_mode: str = Header(..., alias="Compute-Mode", description="Modo computacional: 'CPU' ou 'GPU'"),
    key: str = Depends(validate_api_key)
):
    """
    Configure Ollama compute mode (CPU or GPU)
    
    Headers required:
    - Key: API authentication key  
    - Compute-Mode: "cpu" or "gpu"
    """
    try:
        compute_mode = compute_mode.lower().strip()
        
        if compute_mode not in ["cpu", "gpu"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid compute mode. Must be 'cpu' or 'gpu'"
            )
        
        logger.info(f"🔄 VERBOSE: Switching Ollama compute mode to: {compute_mode.upper()}")
        
        # Save compute mode to environment file
        env_path = "/app/.env"
        env_lines = []
        ollama_config_found = False
        
        # Read existing .env file
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add OLLAMA_COMPUTE_MODE
        for i, line in enumerate(env_lines):
            if line.startswith("OLLAMA_COMPUTE_MODE="):
                env_lines[i] = f"OLLAMA_COMPUTE_MODE={compute_mode}\n"
                ollama_config_found = True
                break
        
        if not ollama_config_found:
            env_lines.append(f"OLLAMA_COMPUTE_MODE={compute_mode}\n")
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        # Set environment variable for current session
        os.environ["OLLAMA_COMPUTE_MODE"] = compute_mode
        
        # Configure Ollama environment variables based on mode
        if compute_mode == "gpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["OLLAMA_GPU_ENABLED"] = "1"
            logger.info(f"🚀 VERBOSE: GPU mode enabled - CUDA devices accessible")
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            os.environ["OLLAMA_GPU_ENABLED"] = "0"
            logger.info(f"🖥️ VERBOSE: CPU mode enabled - GPU disabled")
        
        # Restart Ollama service to apply changes
        import subprocess
        logger.info(f"🔄 VERBOSE: Restarting Ollama service with {compute_mode.upper()} mode...")
        
        try:
            # Stop Ollama
            subprocess.run(['pkill', '-f', 'ollama'], check=False)
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start Ollama with new config
            if compute_mode == "gpu":
                subprocess.Popen(['ollama', 'serve'], env=dict(os.environ))
            else:
                subprocess.Popen(['ollama', 'serve'], env=dict(os.environ))
                
            time.sleep(3)  # Wait for Ollama to start
            
            logger.info(f"✅ VERBOSE: Ollama restarted successfully in {compute_mode.upper()} mode")
            
            return {
                "status": "success",
                "message": f"Compute mode set to {compute_mode.upper()}",
                "compute_mode": compute_mode,
                "gpu_enabled": compute_mode == "gpu",
                "restart_required": False,
                "current_config": {
                    "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
                    "OLLAMA_GPU_ENABLED": os.environ.get("OLLAMA_GPU_ENABLED", "0")
                }
            }
            
        except Exception as restart_error:
            logger.error(f"❌ VERBOSE: Error restarting Ollama: {restart_error}")
            return {
                "status": "success", 
                "message": f"Compute mode set to {compute_mode.upper()} (restart required)",
                "compute_mode": compute_mode,
                "gpu_enabled": compute_mode == "gpu",
                "restart_required": True,
                "note": "Please restart the container to apply changes"
            }
            
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error setting compute mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting compute mode: {str(e)}")

@app.get(
    "/config/compute",
    response_model=ComputeConfigResponse,
    tags=["⚙️ Configuração"],
    summary="Obter modo computacional atual",
    description="Retorna o modo computacional atualmente configurado",
    responses={
        200: {"description": "Configuração obtida com sucesso", "model": ComputeConfigResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def get_compute_mode(
    key: str = Depends(validate_api_key)
):
    """
    Get current Ollama compute mode configuration
    """
    try:
        current_mode = os.environ.get("OLLAMA_COMPUTE_MODE", "cpu")
        gpu_enabled = os.environ.get("OLLAMA_GPU_ENABLED", "0") == "1"
        cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        
        logger.info(f"ℹ️ VERBOSE: Current compute mode: {current_mode.upper()}")
        
        return {
            "status": "success",
            "compute_mode": current_mode,
            "message": f"Current compute mode: {current_mode.upper()}"
        }
        
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error getting compute mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting compute mode: {str(e)}")

@app.get(
    "/",
    tags=["🏠 Informações"],
    summary="Informações da API",
    description="Retorna informações básicas sobre a API",
    responses={
        200: {"description": "Informações da API"},
    }
)
async def root():
    """Root endpoint with API information"""
    current_compute_mode = os.environ.get("OLLAMA_COMPUTE_MODE", "cpu")
    
    return {
        "message": "Document OCR LLM API",
        "version": "1.1.0",
        "current_compute_mode": current_compute_mode.upper(),
        "endpoints": {
            "POST /upload": "🚀 SMART UPLOAD - Auto-detects file type and processes",
            "GET /queue": "Get processing queue status",
            "GET /response/{id}": "Get document response",
            "POST /models/download": "Download new Ollama model",
            "GET /models/list": "List available models",
            "POST /config/compute": "🆕 Set compute mode (CPU/GPU)",
            "GET /config/compute": "🆕 Get current compute mode",
            "GET /health": "Health check"
        },
        "file_types_supported": {
            "Images": "JPG, JPEG, PNG → Tesseract OCR",
            "PDFs": "PDF → PyPDF2 Parser",
            "Word": "DOCX, DOC → python-docx Parser", 
            "Excel": "XLSX, XLS → openpyxl Parser"
        },
        "required_headers": {
            "Key": "API authentication key",
            "Prompt": "Question about the document",
            "Format-Response": "Expected response format",
            "Model": "Ollama model name",
            "Example": "Optional response example",
            "Model-Name": "Model name for download (download endpoint only)",
            "Compute-Mode": "cpu or gpu (compute config endpoint only)"
        }
    }

@app.get(
    "/models/gemini",
    response_model=ModelsListResponse,
    tags=["🤖 Gestão de Modelos"],
    summary="Listar modelos Gemini disponíveis",
    description="Retorna lista de modelos Google Gemini disponíveis",
    responses={
        200: {"description": "Lista de modelos Gemini obtida com sucesso", "model": ModelsListResponse},
        400: {"description": "GEMINI_API_KEY não configurada", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def list_gemini_models_endpoint(
    key: str = Depends(validate_api_key)
):
    """
    🌟 List available Google Gemini models dynamically from API
    
    Headers required:
    - Key: API authentication key
    
    Environment required:
    - GEMINI_API_KEY: Your Google Gemini API key in .env
    
    🔄 **Dynamic Model Fetching:**
    - Fetches live from Google Gemini API
    - Always up-to-date with latest models
    - Automatic filtering for compatible models
    - Sorted by preference (newer models first)
    
    📊 **Response includes:**
    - Model name and description
    - Version information
    - Token limits
    - Recommended model for optimal performance
    
    🚀 **Current Available Models (dynamic):**
    - gemini-2.0-flash: Latest multimodal model
    - gemini-2.5-pro-preview: Most powerful thinking model
    - gemini-1.5-pro: Complex reasoning tasks
    - gemini-1.5-flash: Fast and versatile performance
    - And more as Google releases them!
    """
    try:
        from utils import list_gemini_models
        
        logger.info(f"🌟 VERBOSE: Client requested Gemini models list")
        
        # Validate GEMINI_API_KEY is configured
        if not GEMINI_API_KEY:
            logger.error(f"❌ VERBOSE: GEMINI_API_KEY not configured in environment")
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY not configured in environment"
            )
        
        logger.info(f"🔑 VERBOSE: Using configured Gemini API key (length: {len(GEMINI_API_KEY)})")
        
        # Fetch models dynamically from Google API
        result = await list_gemini_models(GEMINI_API_KEY)
        
        if result['status'] == 'success':
            logger.info(f"✅ VERBOSE: Successfully returned {len(result.get('models', []))} Gemini models")
            logger.info(f"🎯 VERBOSE: Recommended model: {result.get('recommended_model', 'gemini-2.0-flash')}")
            
            # Transform models to match ModelInfo schema
            transformed_models = []
            for model in result.get('models', []):
                transformed_models.append({
                    "name": model.get('name', 'unknown'),
                    "size": model.get('description', None),  # Use description as size info
                    "modified": model.get('version', None),  # Use version as modified info
                    "status": "available"
                })
            
            return {
                "status": "success",
                "provider": "gemini",
                "models": transformed_models
            }
        else:
            logger.warning(f"⚠️ VERBOSE: API call failed, returning fallback models")
            fallback_models_raw = result.get('fallback_models', [
                {"name": "gemini-2.0-flash", "description": "Latest multimodal model", "version": "latest", "size": None, "modified": None, "status": "available"},
                {"name": "gemini-1.5-pro", "description": "Advanced reasoning model", "version": "stable", "size": None, "modified": None, "status": "available"},
                {"name": "gemini-1.5-flash", "description": "Fast performance model", "version": "stable", "size": None, "modified": None, "status": "available"}
            ])
            
            # Transform fallback models to match ModelInfo schema
            transformed_fallback_models = []
            for model in fallback_models_raw:
                transformed_fallback_models.append({
                    "name": model.get('name', 'unknown'),
                    "size": model.get('description', None),  # Use description as size info
                    "modified": model.get('version', None),  # Use version as modified info
                    "status": model.get('status', 'available')
                })
            
            return {
                "status": "success",
                "provider": "gemini",
                "models": transformed_fallback_models
            }
            
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error in models endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Gemini models: {str(e)}"
        )

@app.get(
    "/debug/document/{document_id}",
    tags=["🔧 Debug"],
    summary="Diagnóstico completo de documento",
    description="Endpoint de diagnóstico para verificar problemas de extração e processamento",
    responses={
        200: {"description": "Diagnóstico realizado com sucesso"},
        404: {"description": "Documento não encontrado", "model": ErrorResponse},
        401: {"description": "Chave API inválida", "model": ErrorResponse},
        500: {"description": "Erro interno do servidor", "model": ErrorResponse},
    }
)
async def debug_document(
    document_id: int = Path(..., description="ID do documento"),
    key: str = Depends(validate_api_key)
):
    """
    Diagnóstico completo de um documento para identificar problemas
    """
    try:
        # Get database connection
        database = await get_async_db()
        
        # Get document from database
        query = """
        SELECT id, filename, status, created_at, completed_at, formatted_response, llm_response, error_message,
               model, ai_provider, gemini_api_key, file_type, file_path, prompt, format_response, example,
               extracted_text, full_prompt_sent, updated_at
        FROM documents 
        WHERE id = :document_id
        """
        
        document = await database.fetch_one(query, {"document_id": document_id})
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Diagnóstico completo
        diagnosis = {
            "document_info": {
                "id": document["id"],
                "filename": document["filename"],
                "file_type": document["file_type"],
                "file_path": document["file_path"],
                "status": document["status"],
                "created_at": document["created_at"],
                "updated_at": document["updated_at"],
                "completed_at": document["completed_at"]
            },
            "file_system_check": {},
            "extraction_check": {},
            "processing_check": {},
            "database_check": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # 1. Verificar sistema de arquivos
        file_path = document["file_path"]
        if file_path:
            file_exists = os.path.exists(file_path)
            diagnosis["file_system_check"] = {
                "file_path": file_path,
                "file_exists": file_exists,
                "file_size": os.path.getsize(file_path) if file_exists else 0,
                "file_readable": os.access(file_path, os.R_OK) if file_exists else False
            }
            
            if not file_exists:
                diagnosis["issues_found"].append("CRITICAL: Arquivo não encontrado no sistema de arquivos")
                diagnosis["recommendations"].append("Verificar se o arquivo foi movido ou deletado")
        else:
            diagnosis["issues_found"].append("CRITICAL: Caminho do arquivo não definido")
        
        # 2. Verificar extração de texto
        extracted_text = document["extracted_text"] or ""
        diagnosis["extraction_check"] = {
            "has_extracted_text": bool(extracted_text.strip()),
            "extracted_text_length": len(extracted_text),
            "extracted_text_preview": extracted_text[:200] if extracted_text else None,
            "extraction_tool": get_extraction_tool_name(document["file_type"])
        }
        
        if not extracted_text.strip():
            diagnosis["issues_found"].append("CRITICAL: Texto não foi extraído do documento")
            diagnosis["recommendations"].append("Verificar logs de extração e dependências (tesseract, PyPDF2, etc.)")
        
        # 3. Verificar processamento LLM
        llm_response = document["llm_response"] or ""
        full_prompt = document["full_prompt_sent"] or ""
        diagnosis["processing_check"] = {
            "has_llm_response": bool(llm_response.strip()),
            "llm_response_length": len(llm_response),
            "has_full_prompt": bool(full_prompt.strip()),
            "full_prompt_length": len(full_prompt),
            "ai_provider": document["ai_provider"],
            "model": document["model"]
        }
        
        if not llm_response.strip():
            diagnosis["issues_found"].append("WARNING: LLM não retornou resposta")
            diagnosis["recommendations"].append("Verificar conectividade com Ollama/Gemini")
        
        # 4. Verificar consistência do banco
        status = document["status"]
        diagnosis["database_check"] = {
            "status": status,
            "has_error_message": bool(document["error_message"]),
            "error_message": document["error_message"],
            "has_formatted_response": bool(document["formatted_response"])
        }
        
        # Verificar inconsistências
        if status == "COMPLETED":
            if not extracted_text.strip():
                diagnosis["issues_found"].append("CRITICAL INCONSISTENCY: Status COMPLETED mas texto não extraído")
                diagnosis["recommendations"].append("Reprocessar documento ou verificar pipeline de extração")
            
            if not llm_response.strip():
                diagnosis["issues_found"].append("CRITICAL INCONSISTENCY: Status COMPLETED mas sem resposta LLM")
                diagnosis["recommendations"].append("Verificar processamento LLM")
            
            if not document["formatted_response"]:
                diagnosis["issues_found"].append("WARNING: Status COMPLETED mas sem resposta formatada")
        
        # 5. Tentar re-extração se necessário
        if file_path and os.path.exists(file_path) and not extracted_text.strip():
            try:
                logger.info(f"🔧 DEBUG: Tentando re-extração para documento {document_id}")
                from utils import extract_text_from_file
                re_extracted_text = extract_text_from_file(file_path, document["file_type"])
                
                diagnosis["re_extraction_test"] = {
                    "success": True,
                    "re_extracted_length": len(re_extracted_text),
                    "re_extracted_preview": re_extracted_text[:200] if re_extracted_text else None
                }
                
                if re_extracted_text.strip():
                    diagnosis["recommendations"].append("Re-extração bem-sucedida - considerar reprocessar documento")
                else:
                    diagnosis["issues_found"].append("CRITICAL: Re-extração também falhou - problema com arquivo ou dependências")
                    
            except Exception as e:
                diagnosis["re_extraction_test"] = {
                    "success": False,
                    "error": str(e)
                }
                diagnosis["issues_found"].append(f"CRITICAL: Erro na re-extração: {str(e)}")
        
        # Resumo final
        diagnosis["summary"] = {
            "total_issues": len(diagnosis["issues_found"]),
            "critical_issues": len([i for i in diagnosis["issues_found"] if "CRITICAL" in i]),
            "status": "HEALTHY" if len(diagnosis["issues_found"]) == 0 else "ISSUES_FOUND"
        }
        
        return {
            "status": "success",
            "document_id": document_id,
            "diagnosis": diagnosis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document diagnosis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "status_code": 500
        }
    )

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=DEBUG,
        log_level="info"
    ) 