from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class DocumentStatus(enum.Enum):
    UPLOADED = "uploaded"
    TEXT_EXTRACTED = "text_extracted"
    PROMPT_PROCESSED = "prompt_processed"
    COMPLETED = "completed"
    ERROR = "error"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    
    # Request data
    prompt = Column(Text, nullable=False)
    format_response = Column(Text, nullable=False)
    example = Column(Text, nullable=True)
    model = Column(String(100), nullable=False)
    
    # API Configuration - supports both Ollama and Gemini
    ai_provider = Column(String(20), nullable=True, default="ollama")  # "ollama" or "gemini"
    gemini_api_key = Column(Text, nullable=True)  # Only needed when ai_provider is "gemini"
    
    # Processing results
    extracted_text = Column(Text, nullable=True)
    full_prompt_sent = Column(Text, nullable=True)  # Prompt completo enviado para LLM
    llm_response = Column(Text, nullable=True)
    formatted_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "status": self.status.value if self.status else None,
            "prompt": self.prompt,
            "format_response": self.format_response,
            "example": self.example,
            "model": self.model,
            "ai_provider": self.ai_provider,
            "llm_response": self.llm_response,
            "formatted_response": self.formatted_response,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        } 