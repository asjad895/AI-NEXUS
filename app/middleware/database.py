# Set up database connection
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./faq_pipeline.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "4"))
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Database models
class FAQJob(Base):
    __tablename__ = "faq_jobs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    file_path = Column(String)
    output_path = Column(String, nullable=True)
    status = Column(String)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    entries = relationship("FAQEntry", back_populates="job", cascade="all, delete-orphan")

class FAQEntry(Base):
    __tablename__ = "faq_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("faq_jobs.id"))
    section = Column(String)
    question = Column(Text)
    answer = Column(Text)
    
    job = relationship("FAQJob", back_populates="entries")

class FinetuneJob(Base):
    __tablename__ = "finetune_jobs"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    model = Column(String, nullable=False)
    type = Column(String, nullable=False)
    job_ids = Column(String, nullable=False)
    status = Column(String, nullable=False)
    progress = Column(Integer, default=0)
    message = Column(String)
    model_path = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    estimated_completion = Column(DateTime)

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    role = Column(String, nullable=False) 
    content = Column(String, nullable=False)
    chat_mode = Column(String, default="model")
    timestamp = Column(DateTime, default=datetime.now)

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    agent_id = Column(String, index=True)
    name = Column(String)
    faq_job_ids = Column(String)
    status = Column(String)
    message = Column(Text, nullable=True)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    """
    Get a database session.
    This function creates a new database session for each request
    and closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
