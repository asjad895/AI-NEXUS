"""
ChromaDB Vector Database Client Implementation
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from vector_database import VectorDatabaseClient, DocumentChunk, SearchResult

class ChromaDBClient(VectorDatabaseClient):
    """Client for ChromaDB vector database."""
    
    def __init__(self, 
                host: str = 'localhost', 
                port: int = 8000, 
                persistence_path: Optional[str] = None,
                http_mode: bool = False):
        self.host = host
        self.port = port
        self.persistence_path = persistence_path
        self.http_mode = http_mode
        self._client = None
        self._collections = {}
    
    def connect(self) -> bool:
        """Establish connection to ChromaDB."""
        try:
            if self.http_mode:
                # HTTP client for remote connection
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            else:
                # Persistent client with local storage
                self._client = chromadb.PersistentClient(
                    path=self.persistence_path if self.persistence_path else "./chroma_db"
                )
            
            # Test connection with a simple operation
            self._client.heartbeat()
            return True
        except Exception as e:
            print(f"Failed to connect to ChromaDB: {e}")
            return False
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection in ChromaDB."""
        try:
            # Check if collection exists
            try:
                collection = self._client.get_collection(name=collection_name)
                self._collections[collection_name] = collection
                return True
            except Exception:
                # Collection doesn't exist, create it
                collection = self._client.create_collection(
                    name=collection_name,
                    metadata={"dimension": dimension}
                )
                self._collections[collection_name] = collection
                return True
        except Exception as e:
            print(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from ChromaDB."""
        try:
            self._client.delete_collection(name=collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            return True
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def _get_collection(self, collection_name: str):
        """Helper to get or retrieve a collection reference."""
        if collection_name not in self._collections:
            try:
                self._collections[collection_name] = self._client.get_collection(name=collection_name)
            except Exception as e:
                raise ValueError(f"Collection {collection_name} not found: {e}")
        return self._collections[collection_name]
    
    def ingest_documents(self, 
                        collection_name: str, 
                        documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into ChromaDB."""
        try:
            collection = self._get_collection(collection_name)
            
            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            texts = [doc.text for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # ChromaDB requires unique IDs, so we use upsert to handle duplicates
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Failed to ingest documents into {collection_name}: {e}")
            return False
    
    def search(
        self, 
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in ChromaDB."""
        try:
            collection = self._get_collection(collection_name)
            
            # Convert filters to ChromaDB where clause if provided
            where_clause = filters if filters else None
            
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause
            )
            
            search_results = []
            
            # Process results
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    text = results["documents"][0][i] if results.get("documents") else ""
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    
                    # ChromaDB returns distance, but we want similarity (1 - distance)
                    score = 1.0 - distance
                    
                    search_results.append(SearchResult(
                        id=doc_id,
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
            collection = self._get_collection(collection_name)
            return collection.count()
        except Exception as e:
            print(f"Failed to count documents in {collection_name}: {e}")
            return 0