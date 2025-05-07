"""
API routes for chat-related endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from middleware.logger import logger
from middleware.database import get_db
from middleware.models import ChatRequest, ChatResponse
from finetune_service.finetune import FinetuneService

# Create router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Don't initialize service with a session at module level
# finetune_service = FinetuneService(db=Session())  # Remove this line

@router.post("", response_model=ChatResponse)
def chat_with_model(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with a fine-tuned model.
    """
    try:
        # Create service with the request's db session
        finetune_service = FinetuneService(db=db)
        
        response = finetune_service.chat_with_model(
            request.model_id,
            request.message,
            request.chat_mode,
            request.user_id
        )
        
        return ChatResponse(
            model_id=response["model_id"],
            response=response["response"],
            chat_mode=response["chat_mode"],
            processing_time=response["processing_time"],
            timestamp=response["timestamp"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error chatting with model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error chatting with model: {str(e)}")

@router.get("/history", response_model=List[Dict[str, Any]])
def get_chat_history(
    model_id: str = Query(..., description="Model ID"),
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get chat history for a specific model and user.
    """
    finetune_service = FinetuneService(db=db)
    history = finetune_service.get_chat_history(model_id, user_id)
    return history

@router.delete("/history", response_model=bool)
def clear_chat_history(
    model_id: str = Query(..., description="Model ID"),
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Clear chat history for a specific model and user.
    """
    finetune_service = FinetuneService(db=db)
    result = finetune_service.clear_chat_history(model_id, user_id)
    return result
