
from opik import track
from .base_agents import BaseAgent
from typing import List, Dict, Any, Optional,Type
import openai
from .base_agents import LLMResponse
from pydantic import BaseModel

class OpenAIAgent(BaseAgent):
    """Concrete implementation for OpenAI"""
    
    @track
    def _call_llm_api(self, messages: List[Dict[str, str]],response_model:Type[BaseModel]) -> Dict[str, Any]:
        """Call the OpenAI API"""
        import openai
        
        client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format=response_model
        )
        
        return response.model_dump()
    
    @track
    async def _call_llm_api_async(self, messages: List[Dict[str, str]],response_model: Type[BaseModel]) -> Dict[str, Any]:
        """Call the OpenAI API asynchronously"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format=response_model
        )
        
        return response.model_dump()

