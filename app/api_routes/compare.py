"""
API routes for model comparison endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from middleware.logger import logger
from middleware.database import get_db
from middleware.models import CompareRequest, CompareResponse
from finetune_service.finetune import FinetuneService

# Create router
router = APIRouter(prefix="/api/compare", tags=["compare"])

# Don't initialize service with a session at module level
# finetune_service = FinetuneService(db=Session())  # Remove this line

@router.post("", response_model=CompareResponse)
def compare_answers(request: CompareRequest, db: Session = Depends(get_db)):
    """
    Compare fine-tuned model and RAG answers.
    """
    try:
        # Create service with the request's db session
        finetune_service = FinetuneService(db=db)
        
        response = finetune_service.compare_answers(
            request.model_id,
            request.question,
            request.user_id
        )
        
        return CompareResponse(
            model_id=response["model_id"],
            model_answer=response["model_answer"],
            rag_answer=response["rag_answer"],
            processing_time=response["processing_time"],
            timestamp=response["timestamp"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing answers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing answers: {str(e)}")
