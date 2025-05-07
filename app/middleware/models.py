from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
class Status(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class FAQPipelineRequest(BaseModel):
    file_path: str
    user_id: str

class FAQPipelineResponse(BaseModel):
    job_id: str
    status: Status
    csv_path: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

class FAQEntryModel(BaseModel):
    id: int
    section: str
    question: str
    answer: str
    
    class Config:
        orm_mode = True

# Fine-tuning models
class FinetuneType(str, Enum):
    QA = "qa"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    REASONING = "reasoning"

class FinetuneStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class FinetuneRequest(BaseModel):
    model: str
    type: FinetuneType
    job_ids: List[str]
    user_id: str
    description: Optional[str] = None

class FinetuneResponse(BaseModel):
    id: str
    model: str
    type: FinetuneType
    # job_ids: List[str]
    user_id: str
    status: FinetuneStatus
    progress: Optional[int] = 0
    message: Optional[str] = None
    model_path: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    estimated_completion: Optional[datetime] = None

class FinetuneUpdateRequest(BaseModel):
    model: Optional[str] = None
    type: Optional[FinetuneType] = None
    job_ids: Optional[List[str]] = None
    user_id: Optional[str] = None
    status: Optional[FinetuneStatus] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    model_path: Optional[str] = None
    description: Optional[str] = None
    estimated_completion: Optional[datetime] = None

class ChatRequest(BaseModel):
    model_id: str
    message: str
    chat_mode: str = "model"
    user_id: str

class ChatResponse(BaseModel):
    model_id: str
    response: str
    chat_mode: str
    processing_time: float
    timestamp: datetime = None

class CompareRequest(BaseModel):
    model_id: str
    question: str
    user_id: str

class CompareResponse(BaseModel):
    model_id: str
    model_answer: str
    rag_answer: str
    processing_time: float
    timestamp: datetime = None
