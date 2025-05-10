from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import time
from dotenv import load_dotenv
load_dotenv()
from app.middleware.database import get_db, ChatHistory
from app.middleware.models import Status
from app.Agents.factory import create_smart_agent
from app.Agents.smart_conversation_agent import SmartConversationAgent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from opik import track
from fastapi import Body

router = APIRouter(
    tags=["smart-conversation"],
    responses={404: {"description": "Not found"}},
)

class SmartConversationRequest(BaseModel):
    user_id: str
    message: str
    agent_id: str
    lead_data: Optional[Dict[str, Any]] = None
    missing_lead_data: Optional[Dict[str, str]] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class SmartConversationResponse(BaseModel):
    query_answer: Optional[str] = None
    lead_data: Optional[Dict[str, Any]] = None
    cited_chunks: List[Dict[str, Any]] = []
    processing_time: float
    timestamp: datetime = None

class FAQIngestRequest(BaseModel):
    agent_id: str
    user_id: str
    faq_job_ids: List[str]
class FAQIngestResponse(BaseModel):
    job_id: str
    status: Status
    message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

@router.post("/smart_chat/chat", response_model=SmartConversationResponse)
async def chat_with_smart_agent(
    request: SmartConversationRequest = Body(...)
):
    """
    Chat with the smart conversation agent that can collect lead data and answer queries
    """
    try:
        start_time = time.time()
        
        # agent details
        smart_db_url = os.getenv("AGENT_DB_URL",'sqlite:///smart_agents.db')
        agent_engine = create_engine(smart_db_url)
        AgentSession = sessionmaker(bind=agent_engine)
        agent_db = AgentSession()
        from streamlit_app.pages.smart_agent import SmartAgent as StreamlitSmartAgent
        agent_details = agent_db.query(StreamlitSmartAgent).filter(StreamlitSmartAgent.id == request.agent_id).first()
            
        if not agent_details:
            raise HTTPException(status_code=404, detail=f"Smart agent with ID {request.agent_id} not found")

        smart_agent = create_smart_agent(
            agent_details = agent_details,
            vector_db_type= agent_details.vector_db,
            vector_db_config={"persistence_path": "./chroma_db"},
            
        )
        prev_messages = []
        for i in request.chat_history:
            prev_messages.append({"role": i["role"], "content": i["content"]})
        
        response = await smart_agent.chat(
            user_id=request.user_id,
            message=request.message,
            lead_data=request.lead_data,
            missing_lead_data=request.missing_lead_data,
            chat_history=prev_messages,
            collection_name = f"agent_{request.agent_id}_faqs"
        )
        processing_time = time.time() - start_time
        print(f"final response: {response}")
        return SmartConversationResponse(
            query_answer=response.get("query_answer"),
            lead_data=response.get("lead_data"),
            cited_chunks=response.get("cited_chunks", []),
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with smart agent: {str(e)}")

@router.post("/ingest", response_model=FAQIngestResponse)
async def ingest_faqs(
    background_tasks: BackgroundTasks,
    agent_id: str = Body(...),
    user_id: str = Body(...),
    faq_job_ids: List[str] = Body(...),
    db: Session = Depends(get_db)
):
    request = FAQIngestRequest(
        agent_id=agent_id,
        user_id=user_id,
        faq_job_ids=faq_job_ids
    )
    """
    Ingest FAQs for a smart agent and create vector database collection
    """
    try:
        collection_id = str(uuid.uuid4())
        collection_name = f"agent_{request.agent_id}_faqs"
        
        from app.middleware.database import Collection
        from app.vector_db_service.factory import VectorDBClientFactory
        collection = Collection(
            id=collection_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            name=collection_name,
            faq_job_ids=",".join(request.faq_job_ids),
            status=Status.PENDING,
            message="FAQ ingestion job submitted"
        )
        db.add(collection)
        db.commit()
        vector_db = VectorDBClientFactory()
        client = vector_db.get_client(db_type="chromadb", persistence_path="./chroma_db")
        background_tasks.add_task(
            process_faq_ingest_background,
            collection_details={
                "collection_id": collection_id,
                "agent_id": request.agent_id,
                "user_id": request.user_id,
                "faq_job_ids": request.faq_job_ids,
                "collection_name": collection_name,
                "vector_db":client
            }
        )
        
        return FAQIngestResponse(
            job_id=collection_id, 
            status=Status.PENDING,
            message="FAQ ingestion job submitted",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting FAQ ingestion job: {str(e)}")

@track
def process_faq_ingest_background(collection_details: Dict):
    """
    Background task to process FAQ ingestion
    """
    from app.middleware.database import SessionLocal
    db = SessionLocal()
    smart_db_url = os.getenv("AGENT_DB_URL", "sqlite:///smart_agents.db")
    agent_engine = create_engine(smart_db_url)
    AgentSession = sessionmaker(bind=agent_engine)
    agent_db = AgentSession()
    
    try:
        from app.middleware.database import Collection
        collection = db.query(Collection).filter(Collection.id == collection_details['collection_id']).first()
        collection.status = Status.IN_PROGRESS
        collection.message = "Processing FAQ ingestion"
        db.commit()
        from streamlit_app.pages.smart_agent import SmartAgent as StreamlitSmartAgent
        agent_details = agent_db.query(StreamlitSmartAgent).filter(StreamlitSmartAgent.id == collection_details['agent_id']).first()
        
        if not agent_details:
            raise Exception(f"Smart agent with ID {collection_details['agent_id']} not found")
        from app.middleware.database import FAQEntry
        faq_entries = db.query(FAQEntry).filter(FAQEntry.job_id.in_(collection_details['faq_job_ids'])).all()
        
        if not faq_entries:
            raise Exception(f"No FAQ entries found for the specified job IDs")
        vector_db = collection_details['vector_db']
        vector_db.connect()
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_dimension = 384  
        
        success = vector_db.create_collection(collection_details['collection_name'], embedding_dimension)
        if not success:
            vector_db.delete_collection(collection_details['collection_name'])
            success = vector_db.create_collection(collection_details['collection_name'], embedding_dimension)
            if not success:
                raise Exception(f"Failed to create vector database collection {collection_details['collection_name']}")
        
        from app.vector_db_service.models import DocumentChunk
        chunks = []
        
        for i, faq in enumerate(faq_entries):
            text = f"Q: {faq.question}\nA: {faq.answer}"
            embedding = model.encode(text).tolist()
            
            chunk = DocumentChunk(
                id=f"{faq.id}",
                text=text,
                embedding=embedding,
                metadata={
                    "section": faq.section,
                    "question": faq.question,
                    "chunk_index": i
                }
            )
            chunks.append(chunk)
        
        success = vector_db.ingest_documents(collection_details['collection_name'], chunks)
        if not success:
            raise Exception(f"Failed to ingest documents into collection {collection_details['collection_name']}")
        
        agent_details.collection_name = collection_details['collection_name']
        agent_db.commit()
        
        collection.status = Status.COMPLETED
        collection.message = f"Successfully ingested {len(chunks)} FAQ entries into collection {collection_details['collection_name']}"
        collection.document_count = len(chunks)
        collection.completed_at = datetime.now()
        db.commit()
        
    except Exception as e:
        from app.middleware.database import Collection
        collection = db.query(Collection).filter(Collection.id == collection_details['collection_id']).first()
        if collection:
            collection.status = Status.FAILED
            collection.message = f"Error ingesting FAQs: {str(e)}"
            db.commit()
    finally:
        db.close()
        agent_db.close()

@router.get("/collection/{collection_id}", response_model=FAQIngestResponse)
def get_collection_status(collection_id: str, db: Session = Depends(get_db)):
    """
    Get status of a specific collection.
    """
    from app.middleware.database import Collection
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    return FAQIngestResponse(
        job_id=collection.id,
        status=Status(collection.status),
        message=collection.message,
        created_at=collection.created_at,
        updated_at=collection.updated_at
    )

@router.get("/collections/{agent_id}")
def list_collections(agent_id: str, db: Session = Depends(get_db)):
    """
    List all collections for an agent.
    """
    from app.middleware.database import Collection
    collections = db.query(Collection).filter(Collection.agent_id == agent_id).all()
    
    return {
        "collections": [
            {
                "id": collection.id,
                "name": collection.name,
                "status": collection.status,
                "message": collection.message,
                "document_count": collection.document_count,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at,
                "completed_at": collection.completed_at
            } for collection in collections
        ]
    }


