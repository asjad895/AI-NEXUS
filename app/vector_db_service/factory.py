
from .vector_database import VectorDatabaseClient
from typing import List, Optional, Dict, Any
class VectorDBClientFactory:
    """Factory for creating vector database clients."""
    
    @staticmethod
    def get_client(db_type: str, **kwargs) -> VectorDatabaseClient:
        """
        Get a specific vector database client based on type.
        
        Args:
            db_type: The type of vector database ('qdrant', 'milvus', 'chromadb', 'faiss', 'weaviate')
            **kwargs: Additional connection parameters for the specific database
            
        Returns:
            An instance of the appropriate VectorDatabaseClient
        """
        db_type = db_type.lower()
        
        if db_type == 'qdrant':
            from clients.qdrant import QdrantDBClient
            return QdrantDBClient(**kwargs)
        elif db_type == 'milvus':
            from clients.milvus import MilvusDBClient
            return MilvusDBClient(**kwargs)
        elif db_type == 'chromadb':
            from clients.chromadb import ChromaDBClient
            return ChromaDBClient(**kwargs)
        elif db_type == 'faiss':
            from clients.faiss import FAISSDBClient
            return FAISSDBClient(**kwargs)
        elif db_type == 'weaviate':
            from clients.weaviate import WeaviateDBClient
            return WeaviateDBClient(**kwargs)
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")