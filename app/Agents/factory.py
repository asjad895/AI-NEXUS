from typing import Optional, Dict, Any
from app.Agents_services.base_agents import BaseAgent
from app.Agents.smart_conversation_agent import SmartConversationAgent
from app.vector_db_service.factory import VectorDBClientFactory
from opik import track
from app.Agents_services.factory import create_agent

@track
def create_smart_agent(
    vector_db_type: str = "chromadb",
    vector_db_config: Dict[str, Any] = None,
    collection_prefix: str = "user_faq_",
    embedding_dimension: int = 384,
    max_chunks: int = 5,
    agent_id: str = None,
    agent_details: Dict[str, Any] = None,
) -> SmartConversationAgent:
    
    if vector_db_config is None:
        vector_db_config = {}
    vector_db_layer = VectorDBClientFactory()
    vector_db = vector_db_layer.get_client(vector_db_type, **vector_db_config)
    agent = create_agent(
            llm_provider = agent_details.llm_provider,
            api_key = agent_details.api_key,
            model= agent_details.model,
            base_url = agent_details.base_url
        )
    return SmartConversationAgent(
        llm_agent=agent,
        vector_db_client=vector_db,
        embedding_dimension=embedding_dimension,
        max_chunks=max_chunks
    )