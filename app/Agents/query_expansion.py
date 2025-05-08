
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from opik import track
from app.Agents_services.base_agents import BaseAgent

class QueryExpansionResponse(BaseModel):
    expanded_queries: List[str] = Field(..., description="List of expanded queries with synonyms")

class QueryExpansionAgent:
    """
    Agent that expands user queries with synonyms to improve search results
    while preserving important entities and domain-specific terminology.
    """
    
    def __init__(self, llm_agent: BaseAgent):
        self.llm_agent = llm_agent
        
        self.system_prompt = """
You are a Query Expansion Assistant specialized in generating variations of search queries.

Your task is to generate 5 alternative versions of the user's query by replacing some words with synonyms.

IMPORTANT RULES:
1. Preserve domain-specific terminology (e.g., retail, e-commerce, finance, healthcare terms)
2. Do not change important entities (names, products, brands, locations)
3. Maintain the original intent of the query
4. Each variation should be semantically similar but use different wording
5. Return exactly 5 variations, no more, no less

Format your response as a list of 5 expanded queries, one per line.
"""

    @track
    async def expand_query(self, query: str) -> List[str]:
        """
        Generate 5 synonym variations of the user's query to improve search results
        """
        response = await self.llm_agent.run_async(
            system_prompt=self.system_prompt,
            user_input=f"Original query: {query}\n\nGenerate 5 alternative versions with synonyms:",
            response_model=QueryExpansionResponse
        )
        
        expanded_queries = response.get("expanded_queries", [])
        
        if len(expanded_queries) < 5:
            while len(expanded_queries) < 5:
                expanded_queries.append(query) 
        elif len(expanded_queries) > 5:
            expanded_queries = expanded_queries[:5]
            
        return expanded_queries

