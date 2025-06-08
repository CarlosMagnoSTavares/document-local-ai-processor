from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from database import get_async_db, init_database, close_database, SessionLocal
from models import Document, DocumentStatus
from utils import is_allowed_file, save_uploaded_file, validate_file_size
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

# Create FastAPI app
app = FastAPI(
    title="Document OCR LLM API",
    description="API para análise de documentos com OCR e modelos de linguagem locais",
    version="1.0.0"
)

# Configuration
API_KEY = os.getenv("API_KEY", "your-super-secret-api-key-here")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

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

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    prompt: str = Header(..., alias="Prompt"),
    format_response: str = Header(..., alias="Format-Response"),
    model: str = Header(..., alias="Model"),
    example: Optional[str] = Header(None, alias="Example"),  
    key: str = Depends(validate_api_key)
):
    """
    🚀 SMART UPLOAD - Automatically detects file type and uses appropriate extraction tool
    
    Headers required:
    - Key: API authentication key
    - Prompt: Question to ask about the document
    - Format-Response: Expected response format (e.g., JSON)
    - Model: Ollama model to use (e.g., gemma3:1b, qwen2:0.5b)
    - Example: Optional example of expected response format
    
    📋 Supported file types with automatic detection:
    - Images (JPG, JPEG, PNG) → Tesseract OCR
    - PDFs → PyPDF2 Parser  
    - Word docs (DOCX, DOC) → python-docx Parser
    - Excel files (XLSX, XLS) → openpyxl Parser
    
    🤖 The system automatically:
    1. Detects file extension
    2. Uses appropriate extraction tool
    3. Processes with selected LLM model
    4. Returns formatted response
    """
    try:
        logger.info(f"📤 VERBOSE: Starting document upload process")
        logger.info(f"📁 VERBOSE: Filename: {file.filename}")
        logger.info(f"🤖 VERBOSE: Model requested: {model}")
        logger.info(f"❓ VERBOSE: Prompt: {prompt}")
        
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
        
        return {
            "status": "success",
            "message": "Document uploaded and processing started",
            "document_id": document_id,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/queue")
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

@app.get("/response/{document_id}")
async def get_document_response(
    document_id: int,
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
        SELECT id, filename, status, created_at, completed_at, formatted_response, llm_response, error_message
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
            response_data["response"] = document["formatted_response"]
            response_data["llm_response"] = document["llm_response"]
        elif doc_status in [DocumentStatus.ERROR.value, "ERROR", DocumentStatus.ERROR]:
            response_data["error_message"] = document["error_message"]
        else:
            response_data["message"] = "Document is still being processed"
        
        return {
            "status": "success",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Document OCR LLM API is running"
    }

@app.post("/models/download")
async def download_model(
    model_name: str = Header(..., alias="Model-Name"),
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

@app.get("/models/list")
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
                        models.append({
                            "name": parts[0],
                            "status": "available"
                        })
            
            return {
                "status": "success",
                "models": models,
                "total_models": len(models)
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

@app.post("/config/compute")
async def set_compute_mode(
    compute_mode: str = Header(..., alias="Compute-Mode"),
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

@app.get("/config/compute")
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
            "gpu_enabled": gpu_enabled,
            "cuda_devices": cuda_devices,
            "config": {
                "OLLAMA_COMPUTE_MODE": current_mode,
                "OLLAMA_GPU_ENABLED": os.environ.get("OLLAMA_GPU_ENABLED", "0"),
                "CUDA_VISIBLE_DEVICES": cuda_devices
            }
        }
        
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error getting compute mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting compute mode: {str(e)}")

@app.get("/")
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