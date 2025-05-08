import os
from typing import List, Dict, Any, Optional, Tuple, Type, Union
from pydantic import BaseModel, Field
import json
from opik import track
from app.Agents_services.base_agents import BaseAgent
from app.vector_db_service.vector_database import DocumentChunk, SearchResult
from app.vector_db_service.clients.chromadb import ChromaDBClient
from app.middleware.database import FAQEntry, SessionLocal
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

class LeadData(BaseModel):
    """Model for lead data that needs to be collected"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_company: Optional[str] = None
    skills: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    notice_period: Optional[str] = None
    location: Optional[str] = None
    job_title: Optional[str] = None
    year_of_experience: Optional[str] = None
    education: Optional[str] = None

class SmartConversationResponse(BaseModel):
    """Response model for the smart conversation agent"""
    query_answer: Optional[str] = Field(None, description="Answer to user's query, if any")
    lead_data: Optional[Dict[str, Any]] = Field(None, description="Lead data extracted from user's message")
    cited_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="List of chunks cited in the response")

class SmartConversationAgent:
    """
    Smart Conversation Agent that can collect lead data and answer queries using tools.
    """
    
    def __init__(
        self, 
        llm_agent: BaseAgent,
        vector_db_client: Optional[ChromaDBClient] = None,
        collection_prefix: str = "user_faq_",
        embedding_dimension: int = 384,
        max_chunks: int = 5
    ):
        self.llm_agent = llm_agent
        self.vector_db = vector_db_client or ChromaDBClient(persistence_path="./chroma_db")
        self.vector_db.connect()
        self.collection_prefix = collection_prefix
        self.embedding_dimension = embedding_dimension
        self.max_chunks = max_chunks
        self.db = SessionLocal()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.system_prompt_template = """
You are Nexus Assistant, a helpful and empathetic AI assistant for AI-Nexus.
Your job is to have a natural conversation with the user while:
1. Collecting lead data we need
2. Answering any questions they might have using our knowledge base

LEAD DATA TO COLLECT:
{lead_data_to_collect}

CURRENT LEAD DATA:
{current_lead_data}

TOOLS:
You have access to the following tools:

search_knowledge_base: Search the knowledge base for information to answer user questions
    query: The search query to find relevant information

GUIDELINES:
1. Be conversational and natural - don't sound like a form
2. Only ask for ONE piece of missing lead data at a time
3. If the user asks a question, use the search_knowledge_base tool to find information
4. When using information from the knowledge base, cite sources with numbers like (1), (2)
5. Don't ask for information the user has already provided
6. Extract any lead data the user provides, even if they volunteer it without being asked
7. If all lead data is collected, focus on answering questions and providing value

RESPONSE FORMAT:
Your response must be a valid JSON object with these fields:
- query_answer: Answer to the user's query (null if no query was asked)
- lead_data: Any lead data extracted from this message (null if none)
- cited_chunks: List of chunk IDs you cited in your response (empty list if none)

"""
    
    @track
    async def search_knowledge_base(self, user_id: str, query: str, chat_history: List[Tuple[str, str]] = None) -> List[SearchResult]:
        """
        Search for relevant chunks in the vector database using enhanced queries
        """
        collection_name = f"{self.collection_prefix}{user_id}"
        model = self.embedding_model
        query_embedding = model.encode(query).tolist()
        results = self.vector_db.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            top_k=self.max_chunks
            )
        unique_results = {}
        for result in results:
            if result.id not in unique_results or result.score > unique_results[result.id].score:
                unique_results[result.id] = result
                
        sorted_results = sorted(unique_results.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:self.max_chunks]
    
    @track
    def format_lead_data_to_collect(self, next_lead_data: Dict[str, str]) -> str:
        """
        Format the lead data that needs to be collected
        """
        if not next_lead_data:
            return "All lead data has been collected."
        formatted_data = []
        for field, description in next_lead_data.items():
            formatted_data.append(f"- {field}: {description}")
        return "\n".join(formatted_data)
    
    @track
    def format_current_lead_data(self, lead_data: Dict[str, Any]) -> str:
        """
        Format the current lead data
        """
        if not lead_data or all(v is None for v in lead_data.values()):
            return "No lead data collected yet."
            
        formatted_data = []
        for field, value in lead_data.items():
            if value is not None:
                formatted_data.append(f"- {field}: {value}")
            
        return "\n".join(formatted_data)
    
    @track
    async def process_message(
        self, 
        user_id: str, 
        message: str, 
        lead_data: Dict[str, Any], 
        next_lead_data: Dict[str, str],
        chat_history: List[Tuple[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message, extract lead data, and answer queries
        """
        if chat_history is None:
            chat_history = []
            
        
        # Format lead data information
        formatted_lead_data_to_collect = self.format_lead_data_to_collect(next_lead_data)
        formatted_current_lead_data = self.format_current_lead_data(lead_data)
        
        # Create system prompt
        system_prompt = self.system_prompt_template.format(
            lead_data_to_collect=formatted_lead_data_to_collect,
            current_lead_data=formatted_current_lead_data
        )
        
        # tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search the knowledge base for information to answer user questions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The ambiguity resolved search query to find relevant information"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        response = await self.llm_agent.run_async(
            system_prompt=system_prompt,
            user_input=message,
            chat_history=chat_history,
            tools=tools,
            response_model=SmartConversationResponse
        )
        
        result = {
            "query_answer": response.get("query_answer"),
            "lead_data": response.get("lead_data"),
            "cited_chunks": response.get("cited_chunks", [])
        }
        
        return result
    
    @track
    async def chat(
        self, 
        user_id: str, 
        message: str, 
        lead_data: Dict[str, Any] = None, 
        next_lead_data: Dict[str, str] = None,
        chat_history: List[Tuple[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Main method to chat with the smart conversation agent
        """
        if lead_data is None:
            lead_data = {}
        if next_lead_data is None:
            next_lead_data = {}
            
        # Process the message
        result = await self.process_message(
            user_id=user_id,
            message=message,
            lead_data=lead_data,
            next_lead_data=next_lead_data,
            chat_history=chat_history
        )
        
        return result