from opik import track
from .base_agents import BaseAgent
from typing import List, Dict, Any, Optional

class AnthropicAgent(BaseAgent):
    """Concrete implementation for Anthropic"""
    
    @track
    def _call_llm_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call the Anthropic API but return in OpenAI format"""
        import anthropic
        
        client = anthropic.Anthropic(
            api_key=self.config.api_key
        )
        
        prompt = self._convert_to_anthropic_format(messages)
        
        response = client.completions.create(
            model=self.config.model,
            prompt=prompt,
            max_tokens_to_sample=self.config.max_tokens or 1000,
            temperature=self.config.temperature
        )
        
        return {
            "choices": [
                {
                    "message": {
                        "content": response.completion
                    }
                }
            ]
        }
    
    @track
    async def _call_llm_api_async(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call the Anthropic API asynchronously but return in OpenAI format"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key
        )
        
        prompt = self._convert_to_anthropic_format(messages)
        
        response = await client.completions.create(
            model=self.config.model,
            prompt=prompt,
            max_tokens_to_sample=self.config.max_tokens or 1000,
            temperature=self.config.temperature
        )
        
        return {
            "choices": [
                {
                    "message": {
                        "content": response.completion
                    }
                }
            ]
        }
    
    def _convert_to_anthropic_format(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to Anthropic format"""
        import anthropic
        prompt = ""
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt += f"{anthropic.HUMAN_PROMPT} <system>{content}</system>\n"
            elif role == "user":
                prompt += f"{anthropic.HUMAN_PROMPT} {content}"
            elif role == "assistant":
                prompt += f"{anthropic.AI_PROMPT} {content}"
        
        # Ensure the prompt ends with the AI prompt token
        if not prompt.endswith(anthropic.AI_PROMPT):
            prompt += anthropic.AI_PROMPT
            
        return prompt

