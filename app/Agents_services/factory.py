
from typing import Optional
from .openai import OpenAIAgent
from .anthropic import AnthropicAgent
from .base_agents import BaseAgent

def create_agent(
    llm_provider: str, 
    api_key: str, 
    base_url: Optional[str] = None,
    model: str = None,
    **kwargs
) -> BaseAgent:
    """Factory method to create the appropriate agent based on provider"""
    
    if llm_provider.lower() == "openai":
        model = model
        return OpenAIAgent(llm_provider, api_key, base_url, model, **kwargs)
    elif llm_provider.lower() == "anthropic":
        model = model or "claude-2"
        return AnthropicAgent(llm_provider, api_key, base_url, model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
