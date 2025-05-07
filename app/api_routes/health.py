"""
API routes for health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime

# Create router
router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}