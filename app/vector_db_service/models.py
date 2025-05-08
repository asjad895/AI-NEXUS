from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
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
