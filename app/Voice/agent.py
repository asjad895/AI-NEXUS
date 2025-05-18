from livekit.agents import Agent
from app.prompts.voice import health_agent_prompt
from livekit.agents import Agent, function_tool, get_job_context,ChatContext,RunContext
from livekit.agents import AgentSession
from dataclasses import dataclass
from livekit import api
from livekit.plugins import cartesia
# pronunciation
import re
from livekit import rtc
from livekit.agents.voice import ModelSettings
from livekit.agents import tts
from typing import AsyncIterable

@dataclass
class ShaliniSession:
    user_name: str | None = None
    age: int | None = None
    user_message:str|None = None
    agent_message : str |None = None
    
session = AgentSession[ShaliniSession](
    userdata=ShaliniSession()
)

class HealthAgent(Agent):
    def __init__(self):
        super().__init__(instructions = health_agent_prompt)

    async def on_enter(self) -> None:
        await self.session.say("Hello, I am SHALINI, from MG Care Health solutions. how can I help you today?")
        
    @function_tool()
    async def end_call(self, ctx: RunContext) -> None:
        """Use this tool to indicate that you have collected all the data  and user is completely satisfied or when the user wants to end the conversation, the call should end."""
        await self.session.say(
            instructions=" Summarize the conversation in concise manner , give assurance that we will get back to them soon and end the call with Thank you note."
        )
        job_ctx = get_job_context()
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
        
    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        query: str,
        ) -> str:
        """Search the knowledge base for information related to MG Solution's healthcare domain.
        This tool should be used when a user asks any specific query related to the healthcare domain,
        MG Solution's offerings, limitations, or scope of services. It returns the most semantically
        similar content chunks from the knowledge base to help answer healthcare-specific queries.
    
        Args:
            query: The user's question about MG Solution's healthcare services, domain knowledge,coverage areas, or any healthcare-related inquiries.
        
        """
        pass

    @function_tool()
    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings: ModelSettings
        ) -> AsyncIterable[rtc.AudioFrame]:
        pronunciations = {
            "MG Care Health solutions": "MG Care Health Solutions",
            "SHALINI": "SHA LeeNI",
            "MG": "EM GEE",
            "Care": "Care",
            "Health": "Health",
            "solutions": "Solutions",
        }
    
        async def adjust_pronunciation(input_text: AsyncIterable[str]) -> AsyncIterable[str]:
            async for chunk in input_text:
                modified_chunk = chunk
                
                for term, pronunciation in pronunciations.items():
                    modified_chunk = re.sub(
                        rf'\b{term}\b',
                        pronunciation,
                        modified_chunk,
                        flags=re.IGNORECASE
                    )
                
                yield modified_chunk
        
        async for frame in Agent.default.tts_node(
            self,
            adjust_pronunciation(text),
            model_settings
        ):
            yield frame