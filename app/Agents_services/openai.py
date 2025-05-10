
from opik import track
from .base_agents import BaseAgent
from typing import List, Dict, Any, Optional,Type
import openai
from .base_agents import LLMResponse
from pydantic import BaseModel
import json

class OpenAIAgent(BaseAgent):
    """Concrete implementation for OpenAI"""
    
    @track(type = 'llm')
    def _call_llm_api(self, messages: List[Dict[str, str]],response_model:Type[BaseModel],tools:List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the OpenAI API"""
        import openai
        
        client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = client.beta.chat.completions.parse(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format=response_model,
            tools=tools
        )
        
        return response.model_dump()
    
    @track
    async def _call_llm_api_async(self, messages: List[Dict[str, str]], response_model: Type[BaseModel], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the OpenAI API asynchronously"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response_format = {"type": "json_object"}
        
        try:
            # Make the API call
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format=None,
                tools=tools,
                tool_choice="auto"
            )
            
            # Extract the response content
            content = response.choices[0].message.content
            tool_calls = response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
            
            # Parse the JSON content if it exists
            parsed_content = {}
            if content:
                try:
                    parsed_content = json.loads(content.replace("```",'').replace("json",''))
                except json.JSONDecodeError:
                    parsed_content = {"response": content}
            result = parsed_content
            if tool_calls:
                result["tool_calls"] = []
                for tool_call in tool_calls:
                    tool_call_data = {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                    result["tool_calls"].append(tool_call_data)
                result['message'] = response.choices[0].message
            
            return result
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            raise

