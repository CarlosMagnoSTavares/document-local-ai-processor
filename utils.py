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

async def send_prompt_to_ollama(prompt: str, context: str, model: str, format_response: str = None, example: str = None) -> str:
    """Send prompt to Ollama and get response"""
    try:
        # Build enhanced prompt with strict formatting instructions
        format_instructions = ""
        if format_response and example:
            format_instructions = f"""

CRITICAL FORMATTING INSTRUCTIONS:
- You MUST respond ONLY with the exact JSON format specified below
- DO NOT include any explanations, introductions, or additional text
- DO NOT use markdown formatting or code blocks
- Respond with ONLY the JSON structure, nothing else
- Follow the exact pattern shown in the example

Required JSON Format: {format_response}
Example Response: {example}

Your response must be EXACTLY in this JSON format. No other text is allowed."""
        elif format_response:
            format_instructions = f"""

CRITICAL FORMATTING INSTRUCTIONS:
- You MUST respond ONLY with the exact JSON format specified below
- DO NOT include any explanations, introductions, or additional text
- DO NOT use markdown formatting or code blocks
- Respond with ONLY the JSON structure, nothing else

Required JSON Format: {format_response}

Your response must be EXACTLY in this JSON format. No other text is allowed."""

        full_prompt = f"""Context: {context}

Question: {prompt}{format_instructions}

Based on the context provided above, extract the required information and respond ONLY in the specified JSON format. Do not include any explanations or additional text."""
        
        logger.info(f"🤖 VERBOSE: Sending prompt to Ollama model '{model}'")
        logger.info(f"📄 VERBOSE: Context length: {len(context)} characters")
        logger.info(f"❓ VERBOSE: Prompt: {prompt}")
        if format_response:
            logger.info(f"📋 VERBOSE: Format required: {format_response}")
        if example:
            logger.info(f"💡 VERBOSE: Example provided: {example}")
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
                        "temperature": 0.1,  # Lower temperature for more consistent formatting
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
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
        logger.info(f"🎨 VERBOSE: Starting response formatting")
        logger.info(f"📝 VERBOSE: Original LLM response: {llm_response}")
        logger.info(f"📋 VERBOSE: Expected format: {format_template}")
        
        # Clean the response
        cleaned_response = llm_response.strip()
        
        # Try to extract JSON from the response
        extracted_json = None
        
        # Method 1: Check if the entire response is valid JSON
        try:
            json.loads(cleaned_response)
            extracted_json = cleaned_response
            logger.info(f"✅ VERBOSE: Entire response is valid JSON")
        except json.JSONDecodeError:
            logger.info(f"🔍 VERBOSE: Response is not entirely JSON, attempting extraction")
            
        # Method 2: Try to find JSON within the response
        if extracted_json is None:
            import re
            
            # Look for JSON array patterns [...]
            if format_template.startswith('[') and format_template.endswith(']'):
                json_pattern = r'\[.*?\]'
                json_matches = re.findall(json_pattern, cleaned_response, re.DOTALL)
                
                for match in json_matches:
                    try:
                        json.loads(match)  # Validate JSON
                        extracted_json = match
                        logger.info(f"✅ VERBOSE: Found valid JSON array: {match}")
                        break
                    except json.JSONDecodeError:
                        continue
            
            # Look for JSON object patterns {...}
            elif format_template.startswith('{') and format_template.endswith('}'):
                json_pattern = r'\{.*?\}'
                json_matches = re.findall(json_pattern, cleaned_response, re.DOTALL)
                
                for match in json_matches:
                    try:
                        json.loads(match)  # Validate JSON
                        extracted_json = match
                        logger.info(f"✅ VERBOSE: Found valid JSON object: {match}")
                        break
                    except json.JSONDecodeError:
                        continue
        
        # Method 3: Try to extract specific values based on format template
        if extracted_json is None and format_template:
            logger.info(f"🔧 VERBOSE: Attempting value extraction based on template")
            try:
                # Parse the format template to understand expected structure
                template_obj = json.loads(format_template)
                
                if isinstance(template_obj, list) and len(template_obj) > 0 and isinstance(template_obj[0], dict):
                    # Handle array of objects
                    extracted_data = []
                    for key in template_obj[0].keys():
                        # Try to find values for this key in the response
                        value = extract_value_from_text(cleaned_response, key)
                        if value:
                            extracted_data.append({key: value})
                    
                    if extracted_data:
                        extracted_json = json.dumps(extracted_data, ensure_ascii=False)
                        logger.info(f"✅ VERBOSE: Extracted data based on template: {extracted_json}")
                
                elif isinstance(template_obj, dict):
                    # Handle single object
                    extracted_data = {}
                    for key in template_obj.keys():
                        value = extract_value_from_text(cleaned_response, key)
                        if value:
                            extracted_data[key] = value
                    
                    if extracted_data:
                        extracted_json = json.dumps(extracted_data, ensure_ascii=False)
                        logger.info(f"✅ VERBOSE: Extracted data based on template: {extracted_json}")
                        
            except json.JSONDecodeError:
                logger.warning(f"⚠️ VERBOSE: Could not parse format template as JSON")
        
        # Method 4: Fallback - try to construct response based on example
        if extracted_json is None and example:
            logger.info(f"🔧 VERBOSE: Using example as fallback guidance")
            try:
                example_obj = json.loads(example)
                if isinstance(example_obj, list) and len(example_obj) > 0 and isinstance(example_obj[0], dict):
                    extracted_data = []
                    for key in example_obj[0].keys():
                        value = extract_value_from_text(cleaned_response, key)
                        if value:
                            extracted_data.append({key: value})
                    
                    if extracted_data:
                        extracted_json = json.dumps(extracted_data, ensure_ascii=False)
                        logger.info(f"✅ VERBOSE: Constructed response based on example: {extracted_json}")
            except json.JSONDecodeError:
                logger.warning(f"⚠️ VERBOSE: Could not parse example as JSON")
        
        # Return the best result we found
        if extracted_json:
            logger.info(f"🎉 VERBOSE: Successfully formatted response: {extracted_json}")
            return extracted_json
        else:
            logger.warning(f"⚠️ VERBOSE: Could not extract valid JSON, returning original response")
            return cleaned_response
            
    except Exception as e:
        logger.error(f"❌ VERBOSE: Error formatting response: {e}")
        return llm_response

def extract_value_from_text(text: str, key: str) -> str:
    """Extract a value from text based on a key pattern"""
    import re
    
    # Common patterns to look for
    patterns = [
        # Direct patterns
        rf"{re.escape(key)}:\s*([^\n,}}]+)",
        rf"{re.escape(key)}\s*:\s*([^\n,}}]+)",
        rf"{re.escape(key)}\s*=\s*([^\n,}}]+)",
        
        # Date patterns (if key suggests it's a date)
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        r"(\d{2,4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
        
        # CNPJ patterns
        r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",
        r"(\d{14})",
        
        # General number patterns
        r"(\d+[,\.]\d+)",
        r"(\d+)",
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Clean and return the first match
            value = matches[0].strip()
            # Remove common trailing characters
            value = re.sub(r'[,;\.]+$', '', value)
            if value:
                return value
    
    return None

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