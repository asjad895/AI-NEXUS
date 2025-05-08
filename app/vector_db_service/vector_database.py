"""
Vector Database Service - Core Interfaces and Models
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import numpy as np
from models import DocumentChunk, SearchResult

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
