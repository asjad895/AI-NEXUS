"""
Weaviate Vector Database Client Implementation
"""
from typing import List, Dict, Any, Optional
import weaviate
from app.vector_db_service.vector_database import VectorDatabaseClient, DocumentChunk, SearchResult
class WeaviateDBClient(VectorDatabaseClient):
    """Client for Weaviate vector database."""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 8080,
                 http_host: str = None,
                 api_key: str = None,
                 grpc_port: int = None,
                 https: bool = False):
        self.host = host
        self.port = port
        self.http_host = http_host or f"{'https' if https else 'http'}://{host}:{port}"
        self.api_key = api_key
        self.grpc_port = grpc_port
        self.https = https
        self._client = None
        self.class_prefix = "VectorDB_"
    
    def connect(self) -> bool:
        """Establish connection to Weaviate."""
        try:
            # Configure authentication if API key is provided
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)
            
            # Create client
            self._client = weaviate.Client(
                url=self.http_host,
                auth_client_secret=auth_config,
                additional_headers={"X-OpenAI-Api-Key": self.api_key} if self.api_key else None
            )
            
            # Check if connection is working
            self._client.schema.get()
            return True
        except Exception as e:
            print(f"Failed to connect to Weaviate: {e}")
            return False
    
    def _get_class_name(self, collection_name: str) -> str:
        """Convert collection name to Weaviate class name format."""
        # Weaviate class names must be CamelCase and can't start with a number
        cleaned_name = ''.join(word.capitalize() for word in collection_name.split('_'))
        return f"{self.class_prefix}{cleaned_name}"
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new class in Weaviate."""
        try:
            class_name = self._get_class_name(collection_name)
            
            # Check if class already exists
            schema = self._client.schema.get()
            existing_classes = [cls['class'] for cls in schema.get('classes', [])]
            
            if class_name in existing_classes:
                print(f"Collection {collection_name} (class {class_name}) already exists.")
                return True
            
            # Define class schema
            class_schema = {
                "class": class_name,
                "vectorIndexConfig": {
                    "distance": "cosine"
                },
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "description": "The text content of the document chunk"
                    },
                    {
                        "name": "metadata",
                        "dataType": ["object"],
                        "description": "Metadata associated with the document chunk"
                    }
                ]
            }
            
            # Create class
            self._client.schema.create_class(class_schema)
            return True
        except Exception as e:
            print(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a class from Weaviate."""
        try:
            class_name = self._get_class_name(collection_name)
            
            # Check if class exists before deleting
            schema = self._client.schema.get()
            existing_classes = [cls['class'] for cls in schema.get('classes', [])]
            
            if class_name not in existing_classes:
                print(f"Collection {collection_name} (class {class_name}) does not exist.")
                return True
            
            # Delete class
            self._client.schema.delete_class(class_name)
            return True
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def ingest_documents(self, 
                         collection_name: str, 
                         documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into Weaviate."""
        try:
            class_name = self._get_class_name(collection_name)
            
            # Use batch to efficiently insert documents
            with self._client.batch as batch:
                batch.batch_size = min(100, len(documents))  # Adjust batch size
                
                for doc in documents:
                    # Prepare properties
                    properties = {
                        "text": doc.text,
                        "metadata": doc.metadata
                    }
                    
                    # Add object to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=class_name,
                        uuid=doc.id,
                        vector=doc.embedding
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
        """Search for similar vectors in Weaviate."""
        try:
            class_name = self._get_class_name(collection_name)
            
            # Build query
            query = self._client.query.get(class_name, ["text", "metadata", "_additional {id distance}"])
            
            # Add where filter if provided
            if filters:
                # This is a simplified implementation - Weaviate has more complex filter options
                where_filter = {
                    "path": ["metadata"],
                    "operator": "Equal",
                    "valueObject": filters
                }
                query = query.with_where(where_filter)
            
            # Add vector search
            query = query.with_near_vector({
                "vector": query_vector,
                "certainty": 0.7  # Adjust threshold as needed
            })
            
            # Set limit
            query = query.with_limit(top_k)
            
            # Execute query
            result = query.do()
            
            # Process results
            search_results = []
            if result and "data" in result and "Get" in result["data"] and class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][class_name]:
                    # Extract data
                    item_id = item["_additional"]["id"]
                    text = item.get("text", "")
                    metadata = item.get("metadata", {})
                    
                    # Convert distance to similarity score
                    distance = item["_additional"].get("distance", 0)
                    score = 1.0 - distance  # Convert distance to similarity
                    
                    search_results.append(SearchResult(
                        id=item_id,
                        text=text,
                        score=score,
                        metadata=metadata
                    ))
            
            return search_results
        except Exception as e:
            print(f"Failed to search in {collection_name}: {e}")
            return []
    
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        try:
            class_name = self._get_class_name(collection_name)
            
            # Build aggregate query to count objects
            result = (
                self._client.query
                .aggregate(class_name)
                .with_meta_count()
                .do()
            )
            
            # Extract count from result
            if (result and "data" in result and "Aggregate" in result["data"] and 
                class_name in result["data"]["Aggregate"]):
                return result["data"]["Aggregate"][class_name][0]["meta"]["count"]
            
            return 0
        except Exception as e:
            print(f"Failed to count documents in {collection_name}: {e}")
            return 0