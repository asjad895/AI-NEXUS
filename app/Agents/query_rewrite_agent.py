from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from opik import track
from app.Agents_services.base_agents import BaseAgent

class QueryRewriteResponse(BaseModel):
    rewritten_query: str = Field(..., description="The rewritten query with context from chat history")

class QueryRewriteAgent:
    """
    Agent that rewrites user queries by incorporating context from chat history
    to create more complete and contextual queries.
    """
    
    def __init__(self, llm_agent: BaseAgent):
        self.llm_agent = llm_agent
        
        self.system_prompt = """
You are a Query Rewriting Assistant specialized in enhancing search queries with contextual information.

Your task is to rewrite the user's current query by incorporating relevant context from the chat history.
The goal is to create a more complete, self-contained query that will yield better search results.

IMPORTANT RULES:
1. Maintain the original intent of the current query
2. Incorporate relevant context from previous messages
3. Resolve pronouns and references (e.g., replace "it", "they", "that" with their actual referents)
4. Include important entities and concepts mentioned earlier in the conversation
5. The rewritten query should be a single, coherent sentence or question
6. Do not add information that wasn't in the original query or chat history

Format your response as a single rewritten query.
"""

    @track
    async def rewrite_query(self, current_query: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """
        Rewrite the user's current query by incorporating context from chat history
        """
        if chat_history is None or len(chat_history) == 0:
            return current_query
            
        formatted_history = ""
        for i, (user_msg, assistant_msg) in enumerate(chat_history):
            formatted_history += f"User: {user_msg}\nAssistant: {assistant_msg}\n\n"
            
        user_input = f"""
Chat History:
{formatted_history}

Current Query: {current_query}

Please rewrite the current query to incorporate relevant context from the chat history:
"""
        
        response = await self.llm_agent.run_async(
            system_prompt=self.system_prompt,
            user_input=user_input,
            response_model=QueryRewriteResponse
        )
        
        rewritten_query = response.get("rewritten_query", current_query)
        
        if not rewritten_query or len(rewritten_query.strip()) == 0:
            return current_query
        return rewritten_query
