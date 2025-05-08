# Strategy/Template design pattern code for base agent
from abc import ABC, abstractmethod
from opik import Opik
from opik import track
import time
import asyncio
from typing import List, Tuple, Dict, Any, Optional, Union, Type
import re
import os
import json
import requests
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Initialize Opik for logging
os.environ["OPIK_API_KEY"] = "2Rofpa7vTaP91PL7rkNlp8KHK" 
os.environ["OPIK_WORKSPACE"] = "asjad12"
# opik = Opik(project_name='agent_framework', api_key='2Rofpa7vTaP91PL7rkNlp8KHK', workspace='asjad12')

class LLMResponse(BaseModel):
    """Base response model that all specific response models should inherit from"""
    answer: str

class LLMProviderConfig(BaseModel):
    """Configuration for LLM provider"""
    api_key: str
    base_url: Optional[str] = None
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(
        self, 
        llm_provider: str, 
        api_key: str, 
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ):
        self.config = LLMProviderConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.llm_provider = llm_provider
        self.max_retries = max_retries
    
    @track
    def run(
        self, 
        system_prompt: str, 
        user_input: str, 
        chat_history: List[Tuple[str, str]] = None, 
        response_model: Type[BaseModel] = LLMResponse
    ) -> Dict[str, Any]:
        """Template method that defines the algorithm's skeleton"""
        if chat_history is None:
            chat_history = []
            
        messages = self._prepare_messages(system_prompt, user_input, chat_history)
        
        raw_response = self._get_llm_response_with_retry(messages)
        
        processed_response = self._process_response(raw_response, response_model)
        
        return processed_response
    
    @track
    async def run_async(
        self, 
        system_prompt: str, 
        user_input: str, 
        chat_history: List[Tuple[str, str]] = None, 
        response_model: Type[BaseModel] = LLMResponse
    ) -> Dict[str, Any]:
        """Asynchronous template method that defines the algorithm's skeleton"""
        if chat_history is None:
            chat_history = []
            
        messages = self._prepare_messages(system_prompt, user_input, chat_history)
        
        raw_response = await self._get_llm_response_with_retry_async(messages)
        
        processed_response = self._process_response(raw_response, response_model)
        
        return processed_response
    
    def _prepare_messages(
        self, 
        system_prompt: str, 
        user_input: str, 
        chat_history: List[Tuple[str, str]]
    ) -> List[Dict[str, str]]:
        """Prepare messages in OpenAI format"""
        messages = [{"role": "system", "content": system_prompt}]
        
        for user_msg, assistant_msg in chat_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError))
    )
    @track
    def _get_llm_response_with_retry(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get response from LLM with retry mechanism"""
        try:
            return self._call_llm_api(messages)
        except Exception as e:
            raise
    
    @track
    async def _get_llm_response_with_retry_async(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get response from LLM with retry mechanism (async)"""
        retries = 0
        max_retries = self.max_retries
        wait_time = 2
        
        while True:
            try:
                return await self._call_llm_api_async(messages)
            except (requests.RequestException, ConnectionError, TimeoutError) as e:
                retries += 1
                if retries > max_retries:
                    raise
                
                await asyncio.sleep(wait_time)
                wait_time = min(wait_time * 2, 10)  # Exponential backoff with max of 10 seconds
            except Exception as e:
                raise
    
    @abstractmethod
    def _call_llm_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call the LLM API - to be implemented by concrete agents"""
        pass
    
    @abstractmethod
    async def _call_llm_api_async(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call the LLM API asynchronously - to be implemented by concrete agents"""
        pass
    
    @track
    def _process_response(self, raw_response: Dict[str, Any], response_model: Type[BaseModel]) -> Dict[str, Any]:
        """Process and validate the response"""
        try:
            # Extract content from response
            content = self._extract_content(raw_response)
            
            # Validate with response model
            validated_response = response_model(content=content)
            
            return validated_response.model_dump()
        except ValidationError as e:
            raise
    
    def _extract_content(self, raw_response: Dict[str, Any]) -> str:
        """Extract content from raw response - default implementation for OpenAI format"""
        try:
            return raw_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (KeyError, IndexError) as e:
            return ""

