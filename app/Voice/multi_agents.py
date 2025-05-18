import logging
from typing import Annotated, Optional, List, Dict
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli,JobProcess
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai, silero,neuphonic
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip
from livekit.agents import UserInputTranscribedEvent
from app.Voice.livekit.plugins.sarvam_ai.tts import TTS as custom_sarvam_tts
from app.Voice.utils import(
    Gender,PainSeverity,MedicalData,
    update_address,update_age,update_contact,update_email,update_gender,update_name,update_pain_details,
    update_service_requested,
    add_allergy,add_family_history,add_lifestyle_factor,add_medication,add_notes,add_surgery,add_symptom,
    RunContext_T
)
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents import metrics, MetricsCollectedEvent
import os

usage_collector = metrics.UsageCollector()
llm=openai.LLM.with_cerebras(
        model= os.getenv('VOICE_MODEL_CEREBRAS'),
        api_key=os.getenv('CEREBRAS_API_KEY'),
        temperature=0.7,
        parallel_tool_calls=False,
    )

stt = deepgram.STT(
        api_key=os.getenv('DEEPGRAM_API_KEY'),
        model="nova-3",
    )

# tts = neuphonic.TTS(
#         api_key=os.getenv('NEUPHONIC_API_KEY'),
#         voice_id = os.getenv('NEUPHONIC_TTS'),
#         )

# tts = deepgram.TTS(
#     model="aura-asteria-en",
#     api_key=os.getenv('DEEPGRAM_API_KEY'),
#     )
# tts = cartesia.TTS(
#     voice = os.getenv('CARTESIA_TTS'),
#     api_key=os.getenv('CARTESIA_API_KEY'),
# )

tts = custom_sarvam_tts(
    api_key=os.getenv('SARVAM_API_KEY'),
    target_language_code="en-IN",
    speaker="vidya",
    model="bulbul:v2",
)

print(os.getenv('DEEPGRAM_API_KEY'))

async def log_usage():
    summary = usage_collector.get_summary()
    logger.info(f"Usage: {summary}")

logger = logging.getLogger("mg-care-health-agent")
logger.setLevel(logging.INFO)

load_dotenv()


class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        logger.info(f"entering task {agent_name}")

        userdata: MedicalData = self.session.userdata
        chat_ctx = self.chat_ctx.copy()

        if isinstance(userdata.prev_agent, Agent):
            truncated_chat_ctx = userdata.prev_agent.chat_ctx.copy(
                exclude_instructions=True, exclude_function_call=False
            ).truncate(max_items=6)
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in truncated_chat_ctx.items if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system", 
            content=f"You are {agent_name} agent for MG Care Health Solutions. Current patient data is {userdata.summarize()}",
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply(tool_choice="none")

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> tuple[Agent, str]:
        userdata = context.userdata
        print(f"user data  for agent {name}\n{userdata.summarize()}")
        current_agent = context.session.current_agent
        next_agent = userdata.agents[name]
        userdata.prev_agent = current_agent

        return next_agent, f"Transferring to {name}."


class Greeter(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are SHALINI, a helpful and empathetic medical Voice assistant for MG Care Health Solutions. "
                "Your role is to greet patients warmly, make them feel comfortable, and understand "
                "their primary health concern or what service they're looking for. "
                "Guide them to the right specialist using the appropriate tools."
                "Be conversational and natural - don't sound like a form or robotic."
                "Always use small and short sentences and wait for user response before proceeding."
            ),
        )

    @function_tool()
    async def to_intake(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when we need to collect patient information.
        This function transitions to the intake agent who will collect
        necessary patient details like name, age, gender, contact info, or any userdata"""
        return await self._transfer_to_agent("intake", context)

    @function_tool()
    async def to_specialist(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when the patient wants specific medical information or has a specific medical concern.
        This transitions to the specialist agent who can address specific health queries."""
        return await self._transfer_to_agent("specialist", context)

    @function_tool()
    async def to_summary(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when the conversation is ending and we need to provide a summary.
        This transitions to the summary agent who will recap the conversation."""
        return await self._transfer_to_agent("summary", context)


class IntakeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are SHALINI, an intake Voice specialist at MG Care Health Solutions. "
                "Your job is to collect patient information in a conversational manner and step by step, one by one."
                "Ask for details ONE BY ONE - don't overwhelm the patient with multiple questions at once. "
                "Collect mandatory details: name, age, gender, contact number, email, and address. "
                "If the patient mentions any medical conditions, collect relevant details about those too. "
                "Be empathetic and explain why you need this information - for better care, appointment scheduling, etc. "
                "If patient is hesitating, give helpful engaging reasons like how the details will help with scheduling, prescriptions, maintaining medical history, etc. Your interface with users will be voice. You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
            ),
            tools=[
                update_name, update_age, update_gender, update_contact, 
                update_email, update_address, update_pain_details,
                add_medication, add_symptom, add_allergy, add_surgery,
                add_family_history, add_lifestyle_factor, update_service_requested
            ],
        )

    @function_tool()
    async def check_mandatory_details(self, context: RunContext_T) -> str | tuple[Agent, str]:
        """Called to check if all mandatory details have been collected."""
        userdata = context.userdata
        if userdata.check_mandatory_fields():
            return f"Thank you for providing all the necessary information, {userdata.patient_name}."
        else:
            missing = []
            if not userdata.patient_name:
                missing.append("name")
            if not userdata.patient_age:
                missing.append("age")
            if not userdata.patient_gender:
                missing.append("gender")
            if not userdata.patient_contact:
                missing.append("contact number")
            if not userdata.patient_email:
                missing.append("email")
            if not userdata.patient_address:
                missing.append("address")
            
            return f"We still need to collect some important information: {', '.join(missing)}."

    @function_tool()
    async def to_specialist(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when transitioning to specialist after collecting required information."""
        
        return await self._transfer_to_agent("specialist", context)

    @function_tool()
    async def to_summary(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when the conversation is ending and we need to provide a summary."""
        return await self._transfer_to_agent("summary", context)


class SpecialistAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are SHALINI, a healthcare Voice specialist at MG Care Health Solutions. "
                "Your role is to provide helpful information about health services offered by MG Care Health Solutions. "
                "Answer patient queries related to healthcare with empathy and compassion. "
                "If you don't know specific details about MG Care's services, acknowledge that and offer to "
                "have someone follow up with more information. "
                "Never make up information about medical treatments, services, or diagnoses. "
                "Guide patients to only ask healthcare and MG Care Health Solutions related queries Your interface "
                "with users will be voice. You should use short and concise "
                "responses, and avoiding usage of unpronouncable punctuation."
            ),
            tools=[
                update_pain_details, add_medication, add_symptom, 
                add_allergy, add_surgery, add_family_history, 
                add_lifestyle_factor, update_service_requested, add_notes
            ],
        )

    @function_tool()
    async def to_summary(self, context: RunContext_T) -> tuple[Agent, str]:
        """Called when the conversation is ending and we need to provide a summary."""
        return await self._transfer_to_agent("summary", context)


class SummaryAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are SHALINI, a healthcare Voice assistant at MG Care Health Solutions. "
                "Your role is to provide a concise summary of the conversation with the patient. "
                "Thank the patient for their time and information. "
                "Confirm what will happen next (appointment scheduling, follow-up call, etc.). "
                "End the call professionally and warmly.Your interface "
                "with users will be voice. You should use short and concise "
                "responses, and avoiding usage of unpronouncable punctuation."
            ),
            tools=[],
        )

    @function_tool()
    async def end_conversation(self, context: RunContext_T) -> str:
        """Called to formally end the conversation with a summary."""
        userdata = context.userdata

        summary = f"Thank you for speaking with MG Care Health Solutions today, {userdata.patient_name or 'valued patient'}. "
        
        if userdata.service_requested:
            summary += f"We understand you're interested in {userdata.service_requested}. "
        
        if userdata.pain_location:
            summary += f"We've noted your concerns regarding {userdata.pain_severity or ''} pain in your {userdata.pain_location}. "
        
        if userdata.check_mandatory_fields():
            summary += "We have all your contact information and will reach out to you shortly to schedule your next steps. "
        else:
            summary += "We may need to collect some additional information when we follow up with you. "
        
        summary += "If you have any further questions, please don't hesitate to call us back. Thank you for trusting MG Care Health Solutions with your healthcare needs."
        
        return summary

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    userdata = MedicalData()
    userdata.agents.update(
        {
            "greeter": Greeter(),
            "intake": IntakeAgent(),
            "specialist": SpecialistAgent(),
            "summary": SummaryAgent(),
        }
    )
    
    session = AgentSession[MedicalData](
        userdata=userdata,
        stt= stt,
        llm=llm,
        tts= tts,
        # vad=silero.VAD.load(),
        vad = ctx.proc.userdata["vad"],
        max_tool_steps=5,
    )
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        usage_collector.collect(ev.metrics)
    
    ctx.add_shutdown_callback(log_usage)
    
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        print(f"User input transcribed: {event.transcript}, final: {event.is_final}")
    
    await session.start(
        agent=userdata.agents["greeter"],
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))