
from typing import Optional
from .openai import OpenAIAgent
from .anthropic import AnthropicAgent
from .base_agents import BaseAgent
from opik import track

@track
def create_agent(
    llm_provider: str, 
    api_key: str, 
    base_url: Optional[str] = None,
    model: str = None,
    **kwargs
) -> BaseAgent:
    """Factory method to create the appropriate agent based on provider"""
    
    return OpenAIAgent(llm_provider, api_key, base_url, model, **kwargs)
