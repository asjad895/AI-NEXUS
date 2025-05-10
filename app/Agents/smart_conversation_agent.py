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
    query_answer: Optional[str] = Field(...,description="Answer to user's query, if any")
    lead_data: Optional[Dict[str, Any]] = Field(...,description="Lead data extracted from user's message")
    cited_chunks: List[Dict[str, Any]] = Field(...,default_factory=list, description="List of chunks cited in the response")

class SmartConversationAgent:
    """
    Smart Conversation Agent that can collect lead data and answer queries using tools.
    """
    
    def __init__(
        self, 
        llm_agent: BaseAgent,
        vector_db_client: Optional[ChromaDBClient] = None,
        embedding_dimension: int = 384,
        max_chunks: int = 5
    ):
        self.llm_agent = llm_agent
        self.vector_db = vector_db_client
        self.vector_db.connect()
        self.embedding_dimension = embedding_dimension
        self.max_chunks = max_chunks
        self.db = SessionLocal()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.system_prompt_template = """
You are Hiring Chatbot, a helpful and empathetic AI assistant.
Your job is to have a natural conversation with the user while:
1. Collecting lead data we need ONLY If the user has not provided it before
2. Answering any questions they might have using our knowledge base
3. Always use tool before saying you dont about this or like this.

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
3. If the user asks a query which shows a specific query, use the search_knowledge_base tool to find information
4. When using information from the knowledge base, cite sources with numbers like (1), (2)
5. Don't ask for information the user has already provided
6. Extract any lead data the user provides, even if they volunteer it without being asked
7. If all lead data is collected, focus on answering questions and providing value
8. NEVER respond any query which does not supported or grounded by search_knowledge_base tool, instead guide user what they can ask.
9. Analyze conversation history and if you find any ambiguity in user query, ask for clarification , update "lead_data" with the new information if provided else keep it same.

RESPONSE FORMAT:
Your response must be a valid JSON object which OUGHT to passed by auto json loader with these fields ONLY:
- query_answer: Your next turn response apart from other key (lead_data,cited_chunks)
- lead_data: Any lead data extracted from this message (null if none)
- cited_chunks: List of chunk IDs you cited in your response (empty list if none)
- If you are using tool then not need to return json object, just call the tool with arguments., once you get answer of query then return json object.
"""
    
    @track
    async def search_knowledge_base(self, user_id: str, query: str, chat_history: List[Tuple[str, str]] = None,collection_name = None) -> List[SearchResult]:
        """
        Search for relevant chunks in the vector database using enhanced queries
        """
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
    def format_lead_data_to_collect(self, missing_lead_data: Dict[str, str]) -> str:
        """
        Format the lead data that needs to be collected
        """
        if not missing_lead_data:
            return "All lead data has been collected."
        formatted_data = []
        for field, description in missing_lead_data.items():
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
        missing_lead_data: Dict[str, str],
        chat_history: List[Dict[str, str]] = None,
        collection_name: str = None
    ) -> Dict[str, Any]:
        """
        Process a user message, extract lead data, and answer queries
        """
        if chat_history is None:
            chat_history = []
            
        formatted_lead_data_to_collect = self.format_lead_data_to_collect(missing_lead_data)
        formatted_current_lead_data = self.format_current_lead_data(lead_data)
        
        system_prompt = self.system_prompt_template.format(
            lead_data_to_collect=formatted_lead_data_to_collect,
            current_lead_data=formatted_current_lead_data
        )
        system_prompt += "\n"+"""### Examples:-
user: hi
assistant:
{
    "query_answer": "Hello! How can I assist you today?",
    "lead_data": null,
    "cited_chunks": []
}\n Do Not Append any key in query_answer,this is for your text response only,use other corresponding key"""
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
                                "description": "The complete contextual sentence which should retrieve the best answer from the knowledge base"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        try:
            response = await self.llm_agent.run_async(
                system_prompt=system_prompt,
                user_input=message,
                chat_history=chat_history,
                tools=tools,
                response_model=None
            )
            
            # tool call check
            while 'tool_calls' in response:
                for tool_call in response['tool_calls']:
                    if tool_call['name'] == 'search_knowledge_base':
                        try:
                            arguments = json.loads(tool_call['arguments'])
                            query = arguments['query']
                            tool_call_id = tool_call['id']
                            tool_function_name = "search_knowledge_base"
                        except (json.JSONDecodeError, KeyError):
                            tool_call_id = tool_call['id']
                            tool_function_name = "search_knowledge_base"
                            query = tool_call['arguments'].strip('{}').split(':')[-1].strip(' "\'')
                        
                        search_results = await self.search_knowledge_base(user_id, query, chat_history, collection_name)
                        
                        formatted_results = []
                        for result in search_results:
                            formatted_results.append({
                                "id": result.id,
                                "text": result.text,
                                "score": result.score
                            })
                        
                        chat_history.append({"role":"assistant","content":None,"tool_calls":response['message'].tool_calls})
                        chat_history.append({
                            "role": "tool", 
                            "content": json.dumps(formatted_results,indent = 2),
                            "tool_call_id": tool_call_id,
                            "name": tool_function_name
                        })
                        
                        response = await self.llm_agent.run_async(
                            system_prompt=system_prompt,
                            user_input=message,
                            chat_history=chat_history,
                            tools=tools,
                            response_model=None 
                        )
            
            result = {
                "query_answer": response.get("query_answer"),
                "lead_data": response.get("lead_data"),
                "cited_chunks": response.get("cited_chunks", [])
            }
            
            return result
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {
                "query_answer": f"I'm sorry, I encountered an error while processing your message. Please try again later.",
                "lead_data": None,
                "cited_chunks": []
            }
    
    @track
    async def chat(
        self, 
        user_id: str, 
        message: str, 
        lead_data: Dict[str, Any] = None, 
        missing_lead_data: Dict[str, str] = None,
        chat_history: List[Tuple[str, str]] = None,
        collection_name: str = None
    ) -> Dict[str, Any]:
        """
        Main method to chat with the smart conversation agent
        """
        if lead_data is None:
            lead_data = {}
        if missing_lead_data is None:
            missing_lead_data = {}
            
        result = await self.process_message(
            user_id=user_id,
            message=message,
            lead_data=lead_data,
            missing_lead_data=missing_lead_data,
            chat_history=chat_history,
            collection_name=collection_name
        )
        
        return result
