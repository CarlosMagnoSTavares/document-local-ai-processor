from celery import Celery
from sqlalchemy.orm import Session
from database import SessionLocal, init_database_sync
from models import Document, DocumentStatus
from utils import extract_text_from_file, send_prompt_to_ollama, send_prompt_to_gemini, format_llm_response, cleanup_old_files, list_gemini_models
from loguru import logger
import os
from datetime import datetime
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Initialize database
init_database_sync()

# Create Celery app
celery_app = Celery(
    "document_processor",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(bind=True, max_retries=3)
def extract_text_task(self, document_id: int):
    """Extract text from uploaded file"""
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document with id {document_id} not found")
        
        logger.info(f"🔍 VERBOSE: Starting text extraction for document {document_id}")
        logger.info(f"📁 VERBOSE: File path: {document.file_path}")
        logger.info(f"📄 VERBOSE: File type: {document.file_type}")
        logger.info(f"📝 VERBOSE: Filename: {document.filename}")
        
        # Verificar se o arquivo existe
        if not document.file_path or not os.path.exists(document.file_path):
            error_msg = f"File not found: {document.file_path}"
            logger.error(f"❌ VERBOSE: {error_msg}")
            raise Exception(error_msg)
        
        logger.info(f"✅ VERBOSE: File exists, proceeding with extraction")
        
        # Extract text from file
        extracted_text = extract_text_from_file(document.file_path, document.file_type)
        
        # Verificação crítica do texto extraído
        logger.info(f"🔍 VERBOSE: Extracted text length: {len(extracted_text) if extracted_text else 0}")
        logger.info(f"🔍 VERBOSE: Extracted text preview: {extracted_text[:200] if extracted_text else 'None'}...")
        
        # Verificar se o texto foi realmente extraído
        if not extracted_text or not extracted_text.strip():
            logger.warning(f"⚠️ VERBOSE: No text extracted from file: {document.file_path}")
            logger.warning(f"⚠️ VERBOSE: File type: {document.file_type}")
            logger.warning(f"⚠️ VERBOSE: File exists: {os.path.exists(document.file_path) if document.file_path else False}")
            # Definir texto padrão para evitar problemas
            extracted_text = f"[ERRO: Não foi possível extrair texto do arquivo {document.filename}]"
        
        # CRÍTICO: Atualizar documento no banco com verificação robusta
        logger.info(f"💾 VERBOSE: Saving extracted text to database...")
        logger.info(f"💾 VERBOSE: Text to save length: {len(extracted_text)}")
        
        # Atualizar campos um por um para garantir que sejam salvos
        document.extracted_text = extracted_text
        document.status = DocumentStatus.TEXT_EXTRACTED
        document.updated_at = datetime.utcnow()
        
        # Commit com verificação
        logger.info(f"💾 VERBOSE: Committing to database...")
        db.commit()
        
        # VERIFICAÇÃO CRÍTICA: Refresh e verificar se foi salvo
        db.refresh(document)
        logger.info(f"🔍 VERBOSE: After commit - extracted_text length in DB: {len(document.extracted_text) if document.extracted_text else 0}")
        logger.info(f"🔍 VERBOSE: After commit - status in DB: {document.status}")
        
        # Verificação adicional: fazer nova query para confirmar
        verification_doc = db.query(Document).filter(Document.id == document_id).first()
        if verification_doc:
            logger.info(f"✅ VERBOSE: Verification query - extracted_text length: {len(verification_doc.extracted_text) if verification_doc.extracted_text else 0}")
            logger.info(f"✅ VERBOSE: Verification query - status: {verification_doc.status}")
            
            if not verification_doc.extracted_text:
                logger.error(f"❌ CRITICAL: Text was not saved to database! Attempting manual save...")
                # Tentar salvar novamente
                verification_doc.extracted_text = extracted_text
                verification_doc.status = DocumentStatus.TEXT_EXTRACTED
                verification_doc.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(verification_doc)
                logger.info(f"🔄 VERBOSE: After manual save - extracted_text length: {len(verification_doc.extracted_text) if verification_doc.extracted_text else 0}")
        
        logger.info(f"✅ VERBOSE: Text extraction completed for document {document_id}")
        logger.info(f"📊 VERBOSE: Extracted {len(extracted_text)} characters")
        
        # Chain to next task
        logger.info(f"🔗 VERBOSE: Chaining to prompt processing task")
        process_prompt_task.delay(document_id)
        
        return {"status": "success", "document_id": document_id, "extracted_length": len(extracted_text)}
        
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error extracting text for document {document_id}: {e}")
        logger.error(f"❌ VERBOSE: Exception type: {type(e).__name__}")
        logger.error(f"❌ VERBOSE: Exception details: {str(e)}")
        
        # Update document status to error
        try:
            if 'document' in locals():
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"💾 VERBOSE: Error status saved to database")
        except Exception as db_error:
            logger.error(f"❌ VERBOSE: Failed to save error status: {db_error}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 VERBOSE: Retrying text extraction for document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise e
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def process_prompt_task(self, document_id: int):
    """Process prompt with LLM"""
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document with id {document_id} not found")
        
        logger.info(f"🤖 VERBOSE: Starting prompt processing for document {document_id}")
        logger.info(f"🎯 VERBOSE: Prompt: {document.prompt}")
        logger.info(f"🤖 VERBOSE: Model: {document.model}")
        logger.info(f"🤖 VERBOSE: AI Provider: {document.ai_provider}")
        
        # VERIFICAÇÃO CRÍTICA: Verificar se temos texto extraído
        extracted_text = document.extracted_text or ""
        logger.info(f"📄 VERBOSE: Context length: {len(extracted_text)} characters")
        logger.info(f"📄 VERBOSE: Context preview: {extracted_text[:200] if extracted_text else 'EMPTY'}...")
        
        if not extracted_text.strip():
            logger.error(f"❌ CRITICAL: No extracted text available for document {document_id}")
            logger.error(f"❌ CRITICAL: Document status: {document.status}")
            logger.error(f"❌ CRITICAL: This should not happen if extraction was successful!")
            
            # Tentar recarregar o documento para verificar
            db.refresh(document)
            extracted_text = document.extracted_text or ""
            logger.info(f"🔄 VERBOSE: After refresh - extracted_text length: {len(extracted_text)}")
            
            if not extracted_text.strip():
                logger.warning(f"⚠️ VERBOSE: Still no extracted text - will proceed with empty context")
                logger.warning(f"⚠️ VERBOSE: LLM may use general knowledge instead of document content")
                extracted_text = f"[AVISO: Texto não foi extraído do documento {document.filename}. Responda baseado em conhecimento geral.]"
        
        # Send prompt to appropriate AI provider
        logger.info(f"🔄 VERBOSE: Setting up async event loop for AI call")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if document.ai_provider == "gemini":
                logger.info(f"🌟 VERBOSE: Using Google Gemini API")
                if not document.gemini_api_key:
                    raise Exception("Gemini API key is required for Gemini provider")
                
                llm_response, full_prompt = loop.run_until_complete(
                    send_prompt_to_gemini(
                        document.prompt,
                        extracted_text,
                        document.model,
                        document.gemini_api_key,
                        document.format_response,
                        document.example
                    )
                )
            else:
                logger.info(f"🏠 VERBOSE: Using Ollama (Local)")
                
                # Verificar se Ollama está disponível
                try:
                    import httpx
                    async def check_ollama():
                        async with httpx.AsyncClient(timeout=5) as client:
                            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                            return response.status_code == 200
                    
                    ollama_available = loop.run_until_complete(check_ollama())
                    
                    if not ollama_available:
                        logger.error(f"❌ CRITICAL: Ollama not available at {OLLAMA_BASE_URL}")
                        logger.error(f"❌ CRITICAL: Document will fail unless you:")
                        logger.error(f"  1. Restart Docker container")
                        logger.error(f"  2. Verify Ollama is running inside container")
                        logger.error(f"  3. Or use Gemini provider instead")
                        raise Exception(f"Ollama service not available at {OLLAMA_BASE_URL}")
                        
                except Exception as connectivity_error:
                    logger.error(f"❌ CRITICAL: Failed to connect to Ollama: {connectivity_error}")
                    raise Exception(f"Ollama connectivity error: {connectivity_error}")
                
                llm_response, full_prompt = loop.run_until_complete(
                    send_prompt_to_ollama(
                        document.prompt,
                        extracted_text,
                        document.model,
                        document.format_response,
                        document.example
                    )
                )
        finally:
            loop.close()
        
        # Update document in database
        logger.info(f"💾 VERBOSE: Saving LLM response to database...")
        document.llm_response = llm_response
        document.full_prompt_sent = full_prompt
        document.status = DocumentStatus.PROMPT_PROCESSED
        document.updated_at = datetime.utcnow()
        db.commit()
        
        # Verificação
        db.refresh(document)
        logger.info(f"✅ VERBOSE: LLM response saved - length: {len(document.llm_response) if document.llm_response else 0}")
        
        logger.info(f"✅ VERBOSE: Prompt processing completed for document {document_id}")
        logger.info(f"📊 VERBOSE: LLM response length: {len(llm_response)} characters")
        
        # Chain to next task
        logger.info(f"🔗 VERBOSE: Chaining to response formatting task")
        format_response_task.delay(document_id)
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error processing prompt for document {document_id}: {e}")
        
        # Update document status to error
        try:
            if 'document' in locals():
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error(f"❌ VERBOSE: Failed to save error status: {db_error}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 VERBOSE: Retrying prompt processing for document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise e
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def format_response_task(self, document_id: int):
    """Format and finalize response"""
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document with id {document_id} not found")
        
        logger.info(f"🎨 VERBOSE: Starting response formatting for document {document_id}")
        logger.info(f"📋 VERBOSE: Format template: {document.format_response}")
        logger.info(f"💡 VERBOSE: Example provided: {bool(document.example)}")
        
        # Verificação final do texto extraído
        logger.info(f"🔍 VERBOSE: Final check - extracted_text length: {len(document.extracted_text) if document.extracted_text else 0}")
        
        # Format response
        formatted_response = format_llm_response(
            document.llm_response,
            document.format_response,
            document.example
        )
        
        # Update document in database
        logger.info(f"💾 VERBOSE: Saving final formatted response...")
        document.formatted_response = formatted_response
        document.status = DocumentStatus.COMPLETED
        document.completed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        db.commit()
        
        # Verificação final
        db.refresh(document)
        logger.info(f"✅ VERBOSE: Final verification - status: {document.status}")
        logger.info(f"✅ VERBOSE: Final verification - extracted_text length: {len(document.extracted_text) if document.extracted_text else 0}")
        logger.info(f"✅ VERBOSE: Final verification - formatted_response length: {len(document.formatted_response) if document.formatted_response else 0}")
        
        logger.info(f"🎉 VERBOSE: Response formatting completed for document {document_id}")
        logger.info(f"✅ VERBOSE: Document processing pipeline completed successfully!")
        logger.info(f"📊 VERBOSE: Final response length: {len(formatted_response)} characters")
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error formatting response for document {document_id}: {e}")
        
        # Update document status to error
        try:
            if 'document' in locals():
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error(f"❌ VERBOSE: Failed to save error status: {db_error}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 VERBOSE: Retrying response formatting for document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise e
    finally:
        db.close()

@celery_app.task
def cleanup_task():
    """Periodic cleanup task"""
    try:
        logger.info("Starting cleanup task")
        
        # Clean up old files
        cleanup_old_files()
        
        # Clean up old database records
        db = SessionLocal()
        try:
            from datetime import datetime, timedelta
            
            max_age_hours = int(os.getenv("MAX_RECORD_AGE_HOURS", "24"))
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Delete old completed documents
            deleted_count = db.query(Document).filter(
                Document.completed_at < cutoff_time
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old database records")
            
        finally:
            db.close()
        
        logger.info("Cleanup task completed")
        return {"status": "success", "message": "Cleanup completed"}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise e

# Configure periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'workers.cleanup_task',
        'schedule': crontab(minute=0),  # Run every hour
    },
}

if __name__ == '__main__':
    celery_app.start() 