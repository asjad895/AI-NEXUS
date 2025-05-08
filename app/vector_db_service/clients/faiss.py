"""
FAISS Vector Database Client Implementation
"""
from typing import List, Dict, Any, Optional
import os
import pickle
import numpy as np
import faiss
from pathlib import Path
from app.vector_db_service.vector_database import VectorDatabaseClient, DocumentChunk, SearchResult

class FAISSDBClient(VectorDatabaseClient):
    """
    Client for FAISS vector search library.
    
    Note: FAISS is not a complete database solution but rather a library for
    efficient similarity search. This implementation creates a simple
    database-like interface on top of FAISS with file-based persistence.
    """
    
    def __init__(self, storage_path: str = "./faiss_indexes"):
        self.storage_path = Path(storage_path)
        self.indexes = {}
        self.metadata_store = {}  # Store for document text and metadata
        self.id_map = {}  # Maps document IDs to internal FAISS indices
    
    def connect(self) -> bool:
        """Ensure storage directory exists."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create storage directory: {e}")
            return False
    
    def _get_index_path(self, collection_name: str) -> Path:
        """Get the path to the FAISS index file."""
        return self.storage_path / f"{collection_name}.index"
    
    def _get_metadata_path(self, collection_name: str) -> Path:
        """Get the path to the metadata store file."""
        return self.storage_path / f"{collection_name}.metadata"
    
    def _get_id_map_path(self, collection_name: str) -> Path:
        """Get the path to the ID mapping file."""
        return self.storage_path / f"{collection_name}.idmap"
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new FAISS index."""
        try:
            # Check if index already exists
            index_path = self._get_index_path(collection_name)
            if index_path.exists():
                # Load existing index
                self.indexes[collection_name] = faiss.read_index(str(index_path))
                
                # Load metadata
                metadata_path = self._get_metadata_path(collection_name)
                if metadata_path.exists():
                    with open(metadata_path, 'rb') as f:
                        self.metadata_store[collection_name] = pickle.load(f)
                else:
                    self.metadata_store[collection_name] = {}
                
                # Load ID map
                id_map_path = self._get_id_map_path(collection_name)
                if id_map_path.exists():
                    with open(id_map_path, 'rb') as f:
                        self.id_map[collection_name] = pickle.load(f)
                else:
                    self.id_map[collection_name] = {}
                
                return True
            
            # Create new index - using IndexFlatIP for inner product similarity
            # (cosine similarity can be achieved by normalizing vectors)
            index = faiss.IndexFlatIP(dimension)
            self.indexes[collection_name] = index
            
            # Initialize metadata store and ID map
            self.metadata_store[collection_name] = {}
            self.id_map[collection_name] = {}
            
            # Save empty index, metadata, and ID map
            self._save_index(collection_name)
            self._save_metadata(collection_name)
            self._save_id_map(collection_name)
            
            return True
        except Exception as e:
            print(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def _save_index(self, collection_name: str) -> bool:
        """Save index to disk."""
        try:
            if collection_name in self.indexes:
                index_path = self._get_index_path(collection_name)
                faiss.write_index(self.indexes[collection_name], str(index_path))
                return True
            return False
        except Exception as e:
            print(f"Failed to save index {collection_name}: {e}")
            return False
    
    def _save_metadata(self, collection_name: str) -> bool:
        """Save metadata store to disk."""
        try:
            if collection_name in self.metadata_store:
                metadata_path = self._get_metadata_path(collection_name)
                with open(metadata_path, 'wb') as f:
                    pickle.dump(self.metadata_store[collection_name], f)
                return True
            return False
        except Exception as e:
            print(f"Failed to save metadata for {collection_name}: {e}")
            return False
    
    def _save_id_map(self, collection_name: str) -> bool:
        """Save ID mapping to disk."""
        try:
            if collection_name in self.id_map:
                id_map_path = self._get_id_map_path(collection_name)
                with open(id_map_path, 'wb') as f:
                    pickle.dump(self.id_map[collection_name], f)
                return True
            return False
        except Exception as e:
            print(f"Failed to save ID map for {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a FAISS index and its metadata."""
        try:
            # Remove from memory if loaded
            if collection_name in self.indexes:
                del self.indexes[collection_name]
            
            if collection_name in self.metadata_store:
                del self.metadata_store[collection_name]
                
            if collection_name in self.id_map:
                del self.id_map[collection_name]
            
            # Delete files if they exist
            index_path = self._get_index_path(collection_name)
            if index_path.exists():
                index_path.unlink()
            
            metadata_path = self._get_metadata_path(collection_name)
            if metadata_path.exists():
                metadata_path.unlink()
                
            id_map_path = self._get_id_map_path(collection_name)
            if id_map_path.exists():
                id_map_path.unlink()
            
            return True
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def _load_collection(self, collection_name: str) -> bool:
        """Load collection if not already in memory."""
        try:
            if collection_name not in self.indexes:
                index_path = self._get_index_path(collection_name)
                if not index_path.exists():
                    raise FileNotFoundError(f"Index {collection_name} does not exist")
                
                self.indexes[collection_name] = faiss.read_index(str(index_path))
                
                # Load metadata
                metadata_path = self._get_metadata_path(collection_name)
                if metadata_path.exists():
                    with open(metadata_path, 'rb') as f:
                        self.metadata_store[collection_name] = pickle.load(f)
                else:
                    self.metadata_store[collection_name] = {}
                
                # Load ID map
                id_map_path = self._get_id_map_path(collection_name)
                if id_map_path.exists():
                    with open(id_map_path, 'rb') as f:
                        self.id_map[collection_name] = pickle.load(f)
                else:
                    self.id_map[collection_name] = {}
            
            return True
        except Exception as e:
            print(f"Failed to load collection {collection_name}: {e}")
            return False
    
    def ingest_documents(self, 
                        collection_name: str, 
                        documents: List[DocumentChunk]) -> bool:
        """Ingest multiple document chunks into FAISS."""
        try:
            # Load collection if not already in memory
            if not self._load_collection(collection_name):
                return False
            
            # Get references to index and metadata
            index = self.indexes[collection_name]
            metadata = self.metadata_store[collection_name]
            id_map = self.id_map[collection_name]
            
            # Get current size of index for ID mapping
            current_index_size = index.ntotal
            
            # Prepare embeddings as numpy array and normalize them for cosine similarity
            embeddings = np.array([doc.embedding for doc in documents], dtype=np.float32)
            faiss.normalize_L2(embeddings)
            
            # Add vectors to the index
            index.add(embeddings)
            
            # Update metadata and ID mapping
            for i, doc in enumerate(documents):
                faiss_idx = current_index_size + i
                id_map[doc.id] = faiss_idx
                metadata[faiss_idx] = {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata
                }
            
            # Save updated index and metadata
            self._save_index(collection_name)
            self._save_metadata(collection_name)
            self._save_id_map(collection_name)
            
            return True
        except Exception as e:
            print(f"Failed to ingest documents into {collection_name}: {e}")
            return False
    
    def search(self, 
               collection_name: str,
               query_vector: List[float],
               top_k: int = 10,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar vectors in FAISS."""
        try:
            # Load collection if not already in memory
            if not self._load_collection(collection_name):
                return []
            
            # Get references to index and metadata
            index = self.indexes[collection_name]
            metadata = self.metadata_store[collection_name]
            
            # Convert query to numpy array and normalize
            query_np = np.array([query_vector], dtype=np.float32)
            faiss.normalize_L2(query_np)
            
            # Search for similar vectors
            scores, indices = index.search(query_np, top_k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                # Skip invalid indices
                if idx == -1 or idx not in metadata:
                    continue
                
                doc_data = metadata[idx]
                doc_metadata = doc_data.get("metadata", {})
                
                # Apply filters if provided
                if filters and not self._match_filters(doc_metadata, filters):
                    continue
                
                results.append(SearchResult(
                    id=doc_data["id"],
                    text=doc_data["text"],
                    score=float(score),  # Convert numpy float to Python float
                    metadata=doc_metadata
                ))
            
            return results
        except Exception as e:
            print(f"Failed to search in {collection_name}: {e}")
            return []
    
    def _match_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches all filters."""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def count_documents(self, collection_name: str) -> int:
        """Count the number of documents in a collection."""
        try:
            # Load collection if not already in memory
            if not self._load_collection(collection_name):
                return 0
            
            # Get the index
            index = self.indexes[collection_name]
            return index.ntotal
        except Exception as e:
            print(f"Failed to count documents in {collection_name}: {e}")
            return 0