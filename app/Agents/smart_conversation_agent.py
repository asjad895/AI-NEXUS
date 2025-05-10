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
    response: Optional[str] = Field(...,description="Answer to user's query, if any")
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
<lead_data>
LEAD DATA TO COLLECT:
{lead_data_to_collect}

CURRENT LEAD DATA:
{current_lead_data}

</lead_data>
<lead_data_validation>
You MUST validate the lead data provided by the user. If the lead data is not valid, ask the user to provide the correct data.
number:number should be 10 digit with country code of 3 digit (like +916291259457), if not valid ask to give missing details
email:email should be in valid format (like asjad@gmail.com), if not valid ask to give missing details
money related data : ask currency for complete data.
</lead_data_validation>
TOOLS:
You have access to the following tools:

search_knowledge_base: Search the knowledge base for information to answer user questions
    query: The search query to find relevant information

GUIDELINES:
1. Be conversational and natural - don't sound like a form
2. Only ask for ONE piece of missing lead data at a time
3. If the user asks a query which shows a specific question, use the search_knowledge_base tool to find information
4. When using information from the knowledge base, cite sources with numbers like (1), (2)
5. Don't ask for information the user has already provided
6. Extract any lead data the user provides, even if they volunteer it without being asked
7. If all lead data is collected, focus on answering questions and providing value
8. NEVER respond to any query which is not supported or grounded by the search_knowledge_base tool, instead guide users on what they can ask
9. Analyze conversation history and if you find any ambiguity in user query, ask for clarification
10. Always update and return the lead_data field with all available user information
11. Summarize the conversation once you have collected all the lead data or when the user wants to end the conversation, ending with a Thank you Note
12. Introduce yourself at the beginning of the conversation

IMPORTANT: DO NOT include any JSON structure inside your "response" field. The response field should ONLY contain the plain text message to the user.

RESPONSE STRUCTURE:
Your final output must be valid JSON with exactly these three fields:
- response: Your next message to the user (plain text only, never include JSON, code blocks, or lead_data here)
- lead_data: Dict of all user information collected so far (name, email, etc.)
- cited_chunks: List of chunk IDs cited in your response (empty list if none)
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
    "response": "Hello! How can I assist you today?",
    "lead_data": {"name":"asjad"},
    "cited_chunks": []
}"""
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
            message +='\n Do not add any json structure in "response" key'
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
                        
                        # chat_history.append({"role":"assistant","content":"","tool_calls":response['message'].tool_calls})
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
                "response": response.get("response"),
                "lead_data": response.get("lead_data"),
                "cited_chunks": response.get("cited_chunks", [])
            }
            
            return result
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {
                "response": f"I'm sorry, I encountered an error while processing your message. Please try again later.",
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
