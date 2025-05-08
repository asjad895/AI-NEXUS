from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.middleware.database import get_db, ChatHistory
from app.Agents_services.factory import create_agent
from app.Agents.rag_agent import ConversationalRAGAgent
from app.vector_db_service.clients.chromadb import ChromaDBClient

router = APIRouter(
    prefix="/rag-chat",
    tags=["rag-chat"],
    responses={404: {"description": "Not found"}},
)

class RAGChatRequest(BaseModel):
    user_id: str
    message: str

class RAGChatResponse(BaseModel):
    response: str
    cited_chunks: List[Dict[str, Any]] = []
    processing_time: float
    timestamp: datetime = None

@router.post("", response_model=RAGChatResponse)
async def chat_with_rag(
    request: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with the RAG agent using user's FAQ documents
    """
    try:
        import time
        start_time = time.time()
        
        llm_agent = create_agent(
            llm_provider="openai",
            api_key = '',
            model="gpt-4",
            base_url = ""
        )
        
        vector_db = ChromaDBClient(
            persistence_path="./chroma_db"
        )
        
        rag_agent = ConversationalRAGAgent(
            llm_agent=llm_agent,
            vector_db_client=vector_db
        )
        chat_history_records = db.query(ChatHistory).filter(
            ChatHistory.user_id == request.user_id and ChatHistory.chat_mode == "rag"
        ).order_by(ChatHistory.timestamp.desc()).limit(10).all()
        
        chat_history = []
        for i in range(0, len(chat_history_records) - 1):
            if chat_history_records[i].role == "user":
                user_msg = chat_history_records[i].content
            else:
                assistant_msg = chat_history_records[i].content
            chat_history.append((user_msg, assistant_msg))
        
        # Get response from RAG agent
        response = await rag_agent.chat(
            user_id=request.user_id,
            message=request.message,
            chat_history=chat_history
        )
        
        # Save to chat history
        model_id = "openai"
        user_entry = ChatHistory(
            user_id=request.user_id,
            model_id=model_id,
            role="user",
            content=request.message,
            chat_mode="rag"
        )
        db.add(user_entry)
        
        assistant_entry = ChatHistory(
            user_id=request.user_id,
            model_id="rag-agent",
            role="assistant",
            content=response["content"],
            chat_mode="rag"
        )
        db.add(assistant_entry)
        db.commit()
        
        processing_time = time.time() - start_time
        
        return RAGChatResponse(
            response=response["content"],
            cited_chunks=response["cited_chunks"],
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with RAG agent: {str(e)}")