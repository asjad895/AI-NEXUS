"""
API routes for FAQ-related endpoints.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends, Query, Path
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from typing import List, Optional
from sqlalchemy.orm import Session

from middleware.logger import logger
from middleware.database import get_db, FAQJob, FAQEntry
from middleware.models import Status, FAQPipelineRequest, FAQPipelineResponse, FAQEntryModel
from faq_service.faq import FAQService
from datetime import datetime

# Create router
router = APIRouter(prefix="/api/faq", tags=["faq"])
# faq_service = FAQService(db=Session())  # Remove this line

@router.post("/process", response_model=FAQPipelineResponse)
def process_faq(
    request: FAQPipelineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process FAQ extraction from a markdown file.
    """
    try:
        # Create service with the request's db session
        faq_service = FAQService(db=db)
        
        # Validate input
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail="File not found")
        
        # Create a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job record
        job = FAQJob(
            id=job_id,
            user_id=request.user_id,
            file_path=request.file_path,
            status=Status.PENDING,
            message="Job submitted and pending processing"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Update metrics
        from metrics import PROCESSING_JOBS
        PROCESSING_JOBS.inc()
        logger.info(f"Submitted job {job_id} for processing")

        # Start background processing with a new session
        # Don't pass the request's db session to the background task
        background_tasks.add_task(process_faq_background, job_id, request.file_path)
        
        return FAQPipelineResponse(
            job_id=job_id,
            status=Status.PENDING,
            message="Job submitted and pending processing",
            created_at=job.created_at,
            updated_at=job.updated_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error submitting job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting job: {str(e)}")

def process_faq_background(job_id: str, file_path: str):
    """
    Background task to process FAQ pipeline.
    Creates its own database session.
    """
    # Create a new session for the background task
    from middleware.database import SessionLocal
    db = SessionLocal()
    try:
        faq_service = FAQService(db=db)
        faq_service.process_faq_pipeline(job_id, file_path)
    except Exception as e:
        logger.error(f"Error in background task for job {job_id}: {str(e)}")
    finally:
        db.close()

@router.get("/job/{job_id}", response_model=FAQPipelineResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get status of a specific job.
    """
    job = db.query(FAQJob).filter(FAQJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    return FAQPipelineResponse(
        job_id=job.id,
        status=Status(job.status),
        csv_path=job.output_path,
        message=job.message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.get("/jobs")
def list_jobs(
    user_id: str = Query(..., description="User ID"),
    status: Optional[Status] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all jobs for a user with optional status filter.
    """
    query = db.query(FAQJob).filter(FAQJob.user_id == user_id)
    
    if status:
        query = query.filter(FAQJob.status == status)
    
    jobs = query.all()
    
    return {
        "jobs": [
            FAQPipelineResponse(
                job_id=job.id,
                status=Status(job.status),
                csv_path=job.output_path,
                message=job.message,
                created_at=job.created_at,
                updated_at=job.updated_at
            ) for job in jobs
        ]
    }

@router.post("/job/{job_id}/cancel", response_model=FAQPipelineResponse)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """
    Cancel a specific job.
    """
    job = db.query(FAQJob).filter(FAQJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    if job.status in [Status.PENDING, Status.PROCESSING]:
        job.status = Status.CANCELLED
        job.message = "Job cancelled by user"
        job.updated_at = datetime.now()
        db.commit()
        db.refresh(job)
        
        logger.info(f"Cancelled job {job_id}")
        
        return FAQPipelineResponse(
            job_id=job.id,
            status=Status(job.status),
            csv_path=job.output_path,
            message=job.message,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job.status}")

@router.get("/download/{job_id}")
def download_csv(job_id: str, db: Session = Depends(get_db)):
    """
    Download the generated CSV file.
    """
    job = db.query(FAQJob).filter(FAQJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    if job.status != Status.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {job.status}")
    
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=job.output_path,
        filename=f"faq_dataset_{job_id}.csv",
        media_type="text/csv"
    )

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file and process it.
    """
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("./uploads", exist_ok=True)
        
        # Generate unique filename
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_uuid}{file_extension}"
        file_path = f"./uploads/{unique_filename}"
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create job record
        job_id = str(uuid.uuid4())
        job = FAQJob(
            id=job_id,
            user_id=user_id,
            file_path=file_path,
            status=Status.PENDING,
            message="File uploaded and job submitted"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Submitted job {job_id} for processing")

        # Create service with the request's db session
        faq_service = FAQService(db=db)
        
        # Start background processing
        background_tasks.add_task(process_faq_background, job_id, file_path)
        
        return FAQPipelineResponse(
            job_id=job_id,
            status=Status.PENDING,
            message="File uploaded and job submitted",
            created_at=job.created_at,
            updated_at=job.updated_at
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/entries/{job_id}")
def get_faq_entries(job_id: str, db: Session = Depends(get_db)):
    """
    Get all FAQ entries for a specific job.
    """
    job = db.query(FAQJob).filter(FAQJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    entries = db.query(FAQEntry).filter(FAQEntry.job_id == job_id).all()
    
    return {
        "job_id": job_id,
        "entries": [
            FAQEntryModel(
                id=entry.id,
                section=entry.section,
                question=entry.question,
                answer=entry.answer
            ) for entry in entries
        ]
    }



