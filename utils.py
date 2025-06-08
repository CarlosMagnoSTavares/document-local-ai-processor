import os
import uuid
import pytesseract
from PIL import Image
import PyPDF2
from docx import Document as DocxDocument
import openpyxl
import httpx
import json
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,docx,xlsx,xls,doc").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # Convert MB to bytes

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext.strip().lower() for ext in ALLOWED_EXTENSIONS]

def save_uploaded_file(file_content: bytes, filename: str) -> str:
    """Save uploaded file and return the path"""
    file_extension = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using OCR"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='por+eng')
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image {image_path}: {e}")
        raise

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        raise

def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = DocxDocument(docx_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {docx_path}: {e}")
        raise

def extract_text_from_excel(excel_path: str) -> str:
    """Extract text from Excel file"""
    try:
        workbook = openpyxl.load_workbook(excel_path)
        text = ""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"Sheet: {sheet_name}\n"
            for row in sheet.iter_rows(values_only=True):
                row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    text += row_text + "\n"
            text += "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from Excel {excel_path}: {e}")
        raise

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from file based on its type"""
    file_type = file_type.lower()
    
    logger.info(f"🔍 VERBOSE: Starting text extraction from {file_type.upper()} file: {file_path}")
    
    if file_type in ['jpg', 'jpeg', 'png']:
        logger.info(f"🖼️ VERBOSE: Using OCR (Tesseract) for image processing")
        text = extract_text_from_image(file_path)
    elif file_type == 'pdf':
        logger.info(f"📄 VERBOSE: Using PyPDF2 for PDF processing")
        text = extract_text_from_pdf(file_path)
    elif file_type in ['docx', 'doc']:
        logger.info(f"📝 VERBOSE: Using python-docx for DOCX processing")
        text = extract_text_from_docx(file_path)
    elif file_type in ['xlsx', 'xls']:
        logger.info(f"📊 VERBOSE: Using openpyxl for Excel processing")
        text = extract_text_from_excel(file_path)
    else:
        logger.error(f"❌ VERBOSE: Unsupported file type: {file_type}")
        raise ValueError(f"Unsupported file type: {file_type}")
    
    logger.info(f"✅ VERBOSE: Text extraction completed. Extracted {len(text)} characters")
    logger.info(f"📄 VERBOSE: Text preview: {text[:300]}..." if len(text) > 300 else f"📄 VERBOSE: Full text: {text}")
    
    return text

async def send_prompt_to_ollama(prompt: str, context: str, model: str) -> str:
    """Send prompt to Ollama and get response"""
    try:
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nPlease provide a clear and accurate answer based on the context provided."
        
        logger.info(f"🤖 VERBOSE: Sending prompt to Ollama model '{model}'")
        logger.info(f"📄 VERBOSE: Context length: {len(context)} characters")
        logger.info(f"❓ VERBOSE: Prompt: {prompt}")
        logger.debug(f"📝 VERBOSE: Full prompt: {full_prompt[:500]}..." if len(full_prompt) > 500 else f"📝 VERBOSE: Full prompt: {full_prompt}")
        
        async with httpx.AsyncClient(timeout=300) as client:
            logger.info(f"🔗 VERBOSE: Making request to {OLLAMA_BASE_URL}/api/generate")
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "verbose": True,
                        "temperature": 0.7
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            llm_response = result.get("response", "").strip()
            logger.info(f"✅ VERBOSE: Ollama response received ({len(llm_response)} chars)")
            logger.info(f"💬 VERBOSE: Response preview: {llm_response[:200]}..." if len(llm_response) > 200 else f"💬 VERBOSE: Full response: {llm_response}")
            
            # Log additional Ollama metrics if available
            if "total_duration" in result:
                logger.info(f"⏱️ VERBOSE: Total duration: {result['total_duration']/1e9:.2f}s")
            if "load_duration" in result:
                logger.info(f"⚡ VERBOSE: Load duration: {result['load_duration']/1e9:.2f}s")
            if "prompt_eval_count" in result:
                logger.info(f"🔢 VERBOSE: Prompt tokens: {result['prompt_eval_count']}")
            if "eval_count" in result:
                logger.info(f"📊 VERBOSE: Response tokens: {result['eval_count']}")
            
            return llm_response
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error sending prompt to Ollama: {e}")
        raise

def format_llm_response(llm_response: str, format_template: str, example: str = None) -> str:
    """Format LLM response according to specified format"""
    try:
        # Simple formatting logic - can be enhanced with more sophisticated parsing
        if format_template.startswith('[') and format_template.endswith(']'):
            # JSON array format
            try:
                # Try to parse as JSON to validate format
                json.loads(format_template)
                # For now, return the LLM response wrapped in the expected format
                # This is a simplified implementation - you might want to implement
                # more sophisticated parsing based on your specific needs
                return llm_response
            except json.JSONDecodeError:
                pass
        
        return llm_response
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return llm_response

def cleanup_old_files():
    """Clean up old uploaded files and temporary files"""
    try:
        from datetime import datetime, timedelta
        import glob
        
        max_age_hours = int(os.getenv("MAX_RECORD_AGE_HOURS", "24"))
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean uploads directory
        for file_path in glob.glob(os.path.join(UPLOAD_DIR, "*")):
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {file_path}")
        
        # Clean temp directory
        for file_path in glob.glob(os.path.join(TEMP_DIR, "*")):
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old temp file: {file_path}")
                    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def validate_file_size(file_size: int) -> bool:
    """Validate file size"""
    return file_size <= MAX_FILE_SIZE 