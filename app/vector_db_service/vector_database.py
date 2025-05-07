"""
Vector Database Service - Core Interfaces and Models
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import numpy as np

class DocumentChunk:
    """Represents a document chunk with its embedding vector and metadata."""
    
    def __init__(self, 
                 id: str,
                 text: str, 
                 embedding: List[float], 
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.text = text
        self.embedding = embedding
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"DocumentChunk(id={self.id}, text={self.text[:30]}..., metadata={self.metadata})"


class SearchResult:
    """Standardized search result format."""
    
    def __init__(self, 
                 id: str,
                 text: str,
                 score: float, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.text = text
        self.score = score
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"SearchResult(id={self.id}, score={self.score:.4f}, text={self.text[:30]}...)"


class VectorDatabaseClient(ABC):
    """Abstract interface for all vector database operations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection/index in the database."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection/index from the database."""
        pass
    
    @abstractmethod
    def ingest_documents(self, 
                         collection_name: str, 
                         documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into the database."""
        pass
    
    @abstractmethod
    def search(self, 
               collection_name: str,
               query_vector: List[float],
               top_k: int = 10,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in the database."""
        pass
    
    @abstractmethod
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        pass


class VectorDBService:
    """Main service class for vector database operations."""
    
    def __init__(self, client: VectorDatabaseClient):
        self.client = client
        
    def connect(self) -> bool:
        """Connect to the database."""
        return self.client.connect()
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in the database."""
        return self.client.create_collection(collection_name, dimension)
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the database."""
        return self.client.delete_collection(collection_name)
    
    def ingest_documents(self, 
                          collection_name: str, 
                          documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into the database."""
        return self.client.ingest_documents(collection_name, documents)
    
    def search(self, 
               collection_name: str,
               query_vector: List[float],
               top_k: int = 10,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in the database."""
        return self.client.search(collection_name, query_vector, top_k, filters)
    
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        return self.client.count_documents(collection_name)


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