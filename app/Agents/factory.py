from typing import Optional, Dict, Any
from app.Agents_services.base_agents import BaseAgent
from app.Agents.smart_conversation_agent import SmartConversationAgent
from app.vector_db_service.factory import VectorDBClientFactory

def create_smart_agent(
    llm_agent: BaseAgent,
    vector_db_type: str = "chromadb",
    vector_db_config: Dict[str, Any] = None,
    collection_prefix: str = "user_faq_",
    embedding_dimension: int = 384,
    max_chunks: int = 5,
    agent_id: str = None
) -> SmartConversationAgent:
    """
    Factory method to create a SmartConversationAgent with the specified configuration
    
    Args:
        
        vector_db_type: Type of vector database (chromadb, qdrant)
        vector_db_config: Configuration for the vector database
        collection_prefix: Prefix for collections in the vector database
        embedding_dimension: Dimension of embeddings
        max_chunks: Maximum number of chunks to retrieve
        
    Returns:
        SmartConversationAgent: Configured smart conversation agent
    """
    if vector_db_config is None:
        vector_db_config = {}
    vector_db_layer = VectorDBClientFactory()
    vector_db = vector_db_layer.get_client(vector_db_type, **vector_db_config)
    # Create and return smart conversation agent
    return SmartConversationAgent(
        llm_agent=llm_agent,
        vector_db_client=vector_db,
        collection_prefix=collection_prefix,
        embedding_dimension=embedding_dimension,
        max_chunks=max_chunks
    )