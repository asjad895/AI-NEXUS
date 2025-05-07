"""
API routes for fine-tuning related endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.middleware.logger import logger
from app.middleware.database import get_db
from app.middleware.models import (
    FinetuneType, FinetuneStatus, FinetuneRequest, FinetuneResponse, 
    FinetuneUpdateRequest
)
from app.finetune_service.finetune import FinetuneService

# Create router
router = APIRouter(prefix="/api/finetune", tags=["finetune"])

# Don't initialize service with a session at module level
# Instead, create a new service instance for each request
# finetune_service = FinetuneService(db=Session())  # Remove this line

@router.get("", response_model=List[FinetuneResponse])
def list_finetune_jobs(
    user_id: str = Query(..., description="User ID"),
    status: Optional[FinetuneStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all fine-tuning jobs for a user with optional status filter.
    """
    # Create service with the request's db session
    finetune_service = FinetuneService(db=db)
    jobs = finetune_service.list_finetune_jobs(user_id, status)
    return jobs

@router.post("", response_model=FinetuneResponse)
def create_finetune_job(request: FinetuneRequest, db: Session = Depends(get_db)):
    """
    Create a new fine-tuning job.
    """
    try:
        # Create service with the request's db session
        finetune_service = FinetuneService(db=db)
        job = finetune_service.create_finetune_job(request)
        return job
    except Exception as e:
        logger.error(f"Error creating fine-tuning job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating fine-tuning job: {str(e)}")

@router.get("/{job_id}", response_model=FinetuneResponse)
def get_finetune_job(job_id: str = Path(..., description="Fine-tuning job ID"), db: Session = Depends(get_db)):
    """
    Get details of a specific fine-tuning job.
    """
    # Create service with the request's db session
    finetune_service = FinetuneService(db=db)
    job = finetune_service.get_finetune_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job with ID {job_id} not found")
    
    return job

@router.post("/{job_id}/cancel", response_model=FinetuneResponse)
def cancel_finetune_job(job_id: str = Path(..., description="Fine-tuning job ID"), db: Session = Depends(get_db)):
    """
    Cancel a fine-tuning job.
    """
    # Create service with the request's db session
    finetune_service = FinetuneService(db=db)
    job = finetune_service.cancel_finetune_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job with ID {job_id} not found")
    
    return job

@router.delete("/{job_id}", response_model=bool)
def delete_finetune_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete a fine-tuning job.
    """
    # Create service with the request's db session
    finetune_service = FinetuneService(db=db)
    result = finetune_service.delete_finetune_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job with ID {job_id} not found")
    
    return result

@router.put("/{job_id}", response_model=FinetuneResponse)
def update_finetune_job(
    job_id: str = Path(..., description="Fine-tuning job ID"),
    request: FinetuneUpdateRequest = Body(..., description="Fields to update"),
    db: Session = Depends(get_db)
):
    """
    Update a fine-tuning job with new values.
    """
    try:
        # Create service with the request's db session
        finetune_service = FinetuneService(db=db)
        
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        job = finetune_service.update_finetune_job(job_id, update_data)
        if not job:
            raise HTTPException(status_code=404, detail=f"Fine-tuning job with ID {job_id} not found")
        
        return job
    except Exception as e:
        logger.error(f"Error updating fine-tuning job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating fine-tuning job: {str(e)}")

