"""
Qdrant Vector Database Client Implementation
"""
from typing import List, Dict, Any, Optional
import qdrant_client
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.vector_db_service.vector_database import VectorDatabaseClient, DocumentChunk, SearchResult
class QdrantDBClient(VectorDatabaseClient):
    """Client for Qdrant vector database."""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 6333, 
                 api_key: Optional[str] = None,
                 https: bool = False):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.https = https
        self._client = None
    
    def connect(self) -> bool:
        """Establish connection to Qdrant."""
        try:
            self._client = qdrant_client.QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                https=self.https
            )
            # Test connection with a simple operation
            self._client.get_collections()
            return True
        except Exception as e:
            print(f"Failed to connect to Qdrant: {e}")
            return False
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in Qdrant."""
        try:
            # First check if collection already exists
            collections = self._client.get_collections()
            if collection_name in [col.name for col in collections.collections]:
                print(f"Collection {collection_name} already exists.")
                return True
            
            # Create collection with vector configuration
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE
                )
            )
            return True
        except Exception as e:
            print(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from Qdrant."""
        try:
            self._client.delete_collection(collection_name=collection_name)
            return True
        except UnexpectedResponse as e:
            if "does not exist" in str(e):
                print(f"Collection {collection_name} does not exist.")
                return True  # Consider this successful since the collection doesn't exist
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def ingest_documents(self, 
                         collection_name: str, 
                         documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into Qdrant."""
        try:
            points = []
            for doc in documents:
                points.append(
                    models.PointStruct(
                        id=doc.id,
                        vector=doc.embedding,
                        payload={
                            "text": doc.text,
                            **doc.metadata
                        }
                    )
                )
            
            self._client.upsert(
                collection_name=collection_name,
                points=points
            )
            return True
        except Exception as e:
            print(f"Failed to ingest documents into {collection_name}: {e}")
            return False
    
    def search(self, 
               collection_name: str,
               query_vector: List[float],
               top_k: int = 10,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in Qdrant."""
        try:
            # Convert filters to Qdrant filter format if provided
            filter_condition = None
            if filters:
                # This is a simplified filter conversion logic
                # For complex filters, you might need a more sophisticated approach
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )
            
            search_results = self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter_condition
            )
            
            results = []
            for res in search_results:
                # Extract text and metadata from payload
                text = res.payload.pop("text", "")
                
                results.append(SearchResult(
                    id=res.id,
                    text=text,
                    score=res.score,
                    metadata=res.payload
                ))
            
            return results
        except Exception as e:
            print(f"Failed to search in {collection_name}: {e}")
            return []
    
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        try:
            collection_info = self._client.get_collection(collection_name=collection_name)
            return collection_info.vectors_count
        except Exception as e:
            print(f"Failed to count documents in {collection_name}: {e}")
            return 0