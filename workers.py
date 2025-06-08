from celery import Celery
from sqlalchemy.orm import Session
from database import SessionLocal, init_database_sync
from models import Document, DocumentStatus
from utils import extract_text_from_file, send_prompt_to_ollama, format_llm_response, cleanup_old_files
from loguru import logger
import os
from datetime import datetime
from dotenv import load_dotenv
import asyncio

load_dotenv()

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
    """Extract text from uploaded document"""
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document with id {document_id} not found")
        
        logger.info(f"🔄 VERBOSE: Starting text extraction for document {document_id}")
        logger.info(f"📁 VERBOSE: File path: {document.file_path}")
        logger.info(f"📋 VERBOSE: File type: {document.file_type}")
        
        # Extract text from file
        extracted_text = extract_text_from_file(document.file_path, document.file_type)
        
        # Update document in database
        document.extracted_text = extracted_text
        document.status = DocumentStatus.TEXT_EXTRACTED
        document.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ VERBOSE: Text extraction completed for document {document_id}")
        logger.info(f"📊 VERBOSE: Extracted {len(extracted_text)} characters")
        
        # Chain to next task
        logger.info(f"🔗 VERBOSE: Chaining to prompt processing task")
        process_prompt_task.delay(document_id)
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Error extracting text for document {document_id}: {e}")
        
        # Update document status to error
        if 'document' in locals():
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            document.updated_at = datetime.utcnow()
            db.commit()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying text extraction for document {document_id} (attempt {self.request.retries + 1})")
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
        logger.info(f"📄 VERBOSE: Context length: {len(document.extracted_text)} characters")
        
        # Send prompt to Ollama
        logger.info(f"🔄 VERBOSE: Setting up async event loop for Ollama call")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            llm_response = loop.run_until_complete(
                send_prompt_to_ollama(
                    document.prompt,
                    document.extracted_text,
                    document.model
                )
            )
        finally:
            loop.close()
        
        # Update document in database
        document.llm_response = llm_response
        document.status = DocumentStatus.PROMPT_PROCESSED
        document.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ VERBOSE: Prompt processing completed for document {document_id}")
        logger.info(f"📊 VERBOSE: LLM response length: {len(llm_response)} characters")
        
        # Chain to next task
        logger.info(f"🔗 VERBOSE: Chaining to response formatting task")
        format_response_task.delay(document_id)
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Error processing prompt for document {document_id}: {e}")
        
        # Update document status to error
        if 'document' in locals():
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            document.updated_at = datetime.utcnow()
            db.commit()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying prompt processing for document {document_id} (attempt {self.request.retries + 1})")
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
        
        # Format response
        formatted_response = format_llm_response(
            document.llm_response,
            document.format_response,
            document.example
        )
        
        # Update document in database
        document.formatted_response = formatted_response
        document.status = DocumentStatus.COMPLETED
        document.completed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"🎉 VERBOSE: Response formatting completed for document {document_id}")
        logger.info(f"✅ VERBOSE: Document processing pipeline completed successfully!")
        logger.info(f"📊 VERBOSE: Final response length: {len(formatted_response)} characters")
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Error formatting response for document {document_id}: {e}")
        
        # Update document status to error
        if 'document' in locals():
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            document.updated_at = datetime.utcnow()
            db.commit()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying response formatting for document {document_id} (attempt {self.request.retries + 1})")
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