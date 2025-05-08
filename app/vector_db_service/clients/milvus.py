"""
Milvus Vector Database Client Implementation
"""
from typing import List, Dict, Any, Optional
import random
import string
from app.vector_db_service.vector_database import VectorDatabaseClient, DocumentChunk, SearchResult

from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    MilvusException
)

from vector_database import VectorDatabaseClient, DocumentChunk, SearchResult

class MilvusDBClient(VectorDatabaseClient):
    """Client for Milvus vector database."""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: str = '19530',
                 user: str = '', 
                 password: str = '',
                 secure: bool = False):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.secure = secure
        self.connection_alias = 'default'
        self._collections = {}
    
    def connect(self) -> bool:
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                secure=self.secure,
                asyncio = True
            )
            # Test connection
            return utility.has_connection(self.connection_alias)
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            return False
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in Milvus."""
        try:
            # Check if collection exists
            if utility.has_collection(collection_name):
                print(f"Collection {collection_name} already exists.")
                return True
            
            # Define collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                # For metadata, we'll create specific fields for commonly used types
                FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=65535)
            ]
            
            schema = CollectionSchema(fields=fields)
            
            # Create collection
            collection = Collection(
                name=collection_name,
                schema=schema,
                using=self.connection_alias
            )
            
            # Create index for vector field
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            collection.load()
            return True
        except Exception as e:
            print(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from Milvus."""
        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                
            if collection_name in self._collections:
                del self._collections[collection_name]
                
            return True
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def _get_collection(self, collection_name: str) -> Collection:
        """Helper to get or retrieve a collection reference."""
        if collection_name not in self._collections:
            if not utility.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} does not exist")
            
            self._collections[collection_name] = Collection(
                name=collection_name,
                using=self.connection_alias
            )
            self._collections[collection_name].load()
            
        return self._collections[collection_name]
    
    def ingest_documents(self, 
                         collection_name: str, 
                         documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into Milvus."""
        try:
            collection = self._get_collection(collection_name)
            
            ids = [doc.id for doc in documents]
            texts = [doc.text for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            
            # Convert metadata dictionaries to JSON strings
            import json
            metadata_jsons = [json.dumps(doc.metadata) for doc in documents]
            
            entities = [
                ids,
                texts,
                embeddings,
                metadata_jsons
            ]
            
            collection.insert(entities)
            return True
        except Exception as e:
            print(f"Failed to ingest documents into {collection_name}: {e}")
            return False
    
    def search(self, 
               collection_name: str,
               query_vector: List[float],
               top_k: int = 10,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in Milvus."""
        try:
            collection = self._get_collection(collection_name)
            
            # Prepare search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64}
            }
            
            # Build expression for filtering if provided
            expr = None
            if filters:
                # This is simplified - for complex filters you'd need to build expressions
                # based on available fields and filter values
                import json
                filter_json = json.dumps(filters)
                # Simple string matching for JSON (not very efficient but works for demo)
                expr = f"metadata_json like '%{filter_json.replace('"', '\\"')}%'"
            
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "text", "metadata_json"]
            )
            
            search_results = []
            import json
            
            for hits in results:
                for hit in hits:
                    entity = hit.entity
                    
                    # Parse metadata from JSON string
                    metadata = {}
                    if "metadata_json" in entity:
                        try:
                            metadata = json.loads(entity.get("metadata_json", "{}"))
                        except json.JSONDecodeError:
                            pass
                    
                    search_results.append(SearchResult(
                        id=entity.get("id", ""),
                        text=entity.get("text", ""),
                        score=hit.score, 
                        metadata=metadata
                    ))
            
            return search_results
        except Exception as e:
            print(f"Failed to search in {collection_name}: {e}")
            return []
    
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        try:
            collection = self._get_collection(collection_name)
            return collection.num_entities
        except Exception as e:
            print(f"Failed to count documents in {collection_name}: {e}")
            return 0