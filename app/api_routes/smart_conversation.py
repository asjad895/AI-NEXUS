from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import time
from dotenv import load_dotenv
from app.middleware.database import get_db, ChatHistory
from app.Agents_services.factory import create_agent
from app.Agents.factory import create_smart_agent
from app.Agents.smart_conversation_agent import SmartConversationAgent
from sqlalchemy import create_engine, sessionmaker
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
    chat_history: Optional[List[Dict[str, str]]] = None

class SmartConversationResponse(BaseModel):
    query_answer: Optional[str] = None
    lead_data: Optional[Dict[str, Any]] = None
    cited_chunks: List[Dict[str, Any]] = []
    processing_time: float
    timestamp: datetime = None

@router.post("/{agent_id}", response_model=SmartConversationResponse)
async def chat_with_smart_agent(
    request: SmartConversationRequest,
    agent_id: str = Path(..., description="Agent ID")
):
    """
    Chat with the smart conversation agent that can collect lead data and answer queries
    """
    try:
        start_time = time.time()
        
        # agent details
        smart_db_url = os.getenv("AGENT_DB_URL")
        agent_engine = create_engine(smart_db_url)
        AgentSession = sessionmaker(bind=agent_engine)
        agent_db = AgentSession()
        from streamlit_app.pages.smart_agent import SmartAgent as StreamlitSmartAgent
        agent_details = agent_db.query(StreamlitSmartAgent).filter(StreamlitSmartAgent.id == agent_id).first()
            
        if not agent_details:
            raise HTTPException(status_code=404, detail=f"Smart agent with ID {agent_id} not found")

        agent = create_agent(
            llm_provider = agent_details.llm_provider,
            api_key = agent_details.api_key,
            model= agent_details.model,
            base_url = agent_details.base_url
        )
        smart_agent = create_smart_agent(
            llm_agent = agent,
            vector_db_type= agent_details.vector_db,
            vector_db_config={"persistence_path": "./chroma_db"},
            agent_id=agent_id
            
        )
        prev_messages = []
        for i in request.chat_history:
            if i["role"] == "user":
                user_msg = i["content"]
            else:
                assistant_msg = i["content"]
            prev_messages.append((user_msg, assistant_msg))
        
        response = await smart_agent.chat(
            user_id=request.user_id,
            message=request.message,
            lead_data=request.lead_data,
            next_lead_data=request.next_lead_data,
            chat_history=prev_messages
        )
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
