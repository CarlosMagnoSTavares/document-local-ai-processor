from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases import Database
from models import Base
import os
from dotenv import load_dotenv
import sqlite3
from loguru import logger

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./documents.db")

# Create engines
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
database = Database(DATABASE_URL)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Get async database connection"""
    return database

def get_sync_db():
    """Get sync database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def migrate_database():
    """Migração automática para adicionar campos necessários"""
    try:
        # Conectar ao banco SQLite diretamente
        conn = sqlite3.connect('documents.db')
        cursor = conn.cursor()
        
        # Verificar se o campo full_prompt_sent existe
        cursor.execute('PRAGMA table_info(documents)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Adicionar campo full_prompt_sent se não existir
        if 'full_prompt_sent' not in column_names:
            logger.info("🔧 Adicionando campo full_prompt_sent ao banco de dados...")
            cursor.execute('ALTER TABLE documents ADD COLUMN full_prompt_sent TEXT')
            conn.commit()
            logger.info("✅ Campo full_prompt_sent adicionado com sucesso")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração do banco: {e}")

async def init_database():
    """Initialize database connection"""
    from models import Base
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Executar migração
    migrate_database()
    
    # Connect to database
    await database.connect()
    logger.info("Database connected successfully")

def init_database_sync():
    """Initialize database connection synchronously (for Celery workers)"""
    from models import Base
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Executar migração
    migrate_database()
    
    logger.info("Database initialized synchronously")

async def close_database():
    """Close database connection"""
    await database.disconnect()
    logger.info("Database disconnected") 