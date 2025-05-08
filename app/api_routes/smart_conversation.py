from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from app.middleware.database import get_db, ChatHistory, SmartAgent
from app.Agents_services.factory import create_agent
from app.Agents.factory import create_smart_agent
from app.Agents.smart_conversation_agent import SmartConversationAgent

router = APIRouter(
    prefix="/smart-conversation",
    tags=["smart-conversation"],
    responses={404: {"description": "Not found"}},
)

class SmartConversationRequest(BaseModel):
    user_id: str
    message: str
    lead_data: Optional[Dict[str, Any]] = None
    next_lead_data: Optional[Dict[str, str]] = None

class SmartConversationResponse(BaseModel):
    query_answer: Optional[str] = None
    lead_data: Optional[Dict[str, Any]] = None
    cited_chunks: List[Dict[str, Any]] = []
    processing_time: float
    timestamp: datetime = None

@router.post("", response_model=SmartConversationResponse)
async def chat_with_smart_agent(
    request: SmartConversationRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with the smart conversation agent that can collect lead data and answer queries
    """
    try:
        import time
        import os
        start_time = time.time()
        
        # Create LLM agent
        agent = create_agent(
            llm_provider="openai",
            api_key = 'AIzaSyDqup56c1zet2r0ji9Yk1REot8GehO5Jac',
            model="gemini-2.0-flash",
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        smart_agent = create_smart_agent(
            llm_agent = agent,
            vector_db_type="chromadb",
            vector_db_config={"persistence_path": "./chroma_db"}
            
        )
        
        chat_history_records = db.query(ChatHistory).filter(
            ChatHistory.user_id == request.user_id
        ).order_by(ChatHistory.timestamp.desc()).limit(10).all()
        
        chat_history = []
        for i in range(0, len(chat_history_records) - 1):
            if chat_history_records[i].role == "user":
                user_msg = chat_history_records[i].content
            else:
                assistant_msg = chat_history_records[i].content
            chat_history.append((user_msg, assistant_msg))
        
        response = await smart_agent.chat(
            user_id=request.user_id,
            message=request.message,
            lead_data=request.lead_data,
            next_lead_data=request.next_lead_data,
            chat_history=chat_history
        )
        
        user_entry = ChatHistory(
            user_id=request.user_id,
            model_id="smart-agent",
            role="user",
            content=request.message,
            chat_mode="smart"
        )
        db.add(user_entry)
        
        assistant_entry = ChatHistory(
            user_id=request.user_id,
            model_id="smart-agent",
            role="assistant",
            content=response["response"],
            chat_mode="smart"
        )
        db.add(assistant_entry)
        db.commit()
        
        processing_time = time.time() - start_time
        
        return SmartConversationResponse(
            query_answer=response.get("query_answer"),
            lead_data=response.get("lead_data"),
            cited_chunks=response.get("cited_chunks", []),
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with smart agent: {str(e)}")
