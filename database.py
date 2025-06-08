from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases import Database
from models import Base
import os
from dotenv import load_dotenv

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
    return database

async def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    await database.connect()

def init_database_sync():
    """Initialize database tables synchronously"""
    Base.metadata.create_all(bind=engine)

async def close_database():
    """Close database connection"""
    await database.disconnect() 