"""Fine-tuning service for model training and management.
"""
import os
import time
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.middleware.logger import logger
from app.middleware.database import FinetuneJob, ChatHistory
from app.middleware.models import FinetuneStatus, FinetuneType, FinetuneRequest, FinetuneResponse

class FinetuneService:
    def __init__(self, db: Session):
        """
        Initialize the service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_finetune_job(self, request: FinetuneRequest) -> FinetuneResponse:
        """        
        Create a new fine-tuning job.
        """
        try:
            # Generate a unique ID for the job
            job_id = str(uuid.uuid4())
            
            # Create job record
            job = FinetuneJob(
                id=job_id,
                user_id=request.user_id,
                model=request.model,
                type=request.type,
                job_ids=",".join(request.job_ids),
                status=FinetuneStatus.PENDING,
                progress=0,
                message="Job submitted and pending processing",
                description=request.description,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                estimated_completion=datetime.now() + timedelta(hours=3)
            )
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"Created new fine-tuning job: {job_id}")
            
            # background task for fine tuning 
            
            return FinetuneResponse(
                id=job.id,
                model=job.model,
                type=job.type,
                # job_ids=request.job_ids,
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                model_path=job.model_path,
                description=job.description,
                created_at=job.created_at,
                updated_at=job.updated_at,
                estimated_completion=job.estimated_completion
            )
        except Exception as e:
            logger.error(f"Error creating fine-tuning job: {str(e)}")
            raise e
    
    def get_finetune_job(self, job_id: str) -> Optional[FinetuneResponse]:
        """
        Get details of a specific fine-tuning job.
        """
        try:
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == job_id).first()
            
            if not job:
                return None
            
            return FinetuneResponse(
                id=job.id,
                model=job.model,
                type=job.type,
                job_ids=job.job_ids.split(",") if job.job_ids else [],
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                model_path=job.model_path,
                description=job.description,
                created_at=job.created_at,
                updated_at=job.updated_at,
                estimated_completion=job.estimated_completion
            )
        except Exception as e:
            logger.error(f"Error getting fine-tuning job {job_id}: {str(e)}")
            raise e
    
    def list_finetune_jobs(self, user_id: str, status: Optional[FinetuneStatus] = None) -> List[FinetuneResponse]:
        """
        List all fine-tuning jobs for a user with optional status filter.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            List of fine-tuning jobs
        """
        try:
            query = self.db.query(FinetuneJob).filter(FinetuneJob.user_id == user_id)
            
            if status:
                query = query.filter(FinetuneJob.status == status)
            
            jobs = query.all()
            
            return [
                FinetuneResponse(
                    id=job.id,
                    user_id=job.user_id,
                    model=job.model,
                    type=job.type,
                    status=job.status,
                    progress=job.progress,
                    message=job.message,
                    description=job.description,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    estimated_completion=job.estimated_completion
                ) for job in jobs
            ]
        except Exception as e:
            logger.error(f"Error listing fine-tuning jobs for user {user_id}: {str(e)}")
            raise e
    
    def cancel_finetune_job(self, job_id: str) -> Optional[FinetuneResponse]:
        """
        Cancel a fine-tuning job.
        """
        try:
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == job_id).first()
            
            if not job:
                return None
            
            # Only allow cancellation of pending or processing jobs
            if job.status not in [FinetuneStatus.PENDING, FinetuneStatus.PROCESSING]:
                raise ValueError(f"Cannot cancel job with status {job.status}")
            
            job.status = FinetuneStatus.CANCELLED
            job.message = "Job cancelled by user"
            job.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"Cancelled fine-tuning job {job_id}")
            
            return FinetuneResponse(
                id=job.id,
                model=job.model,
                type=job.type,
                # job_ids=job.job_ids.split(",") if job.job_ids else [],
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                model_path=job.model_path,
                description=job.description,
                created_at=job.created_at,
                updated_at=job.updated_at,
                estimated_completion=job.estimated_completion
            )
        except Exception as e:
            logger.error(f"Error cancelling fine-tuning job {job_id}: {str(e)}")
            raise e
    
    def delete_finetune_job(self, job_id: str) -> bool:
        """
        Delete a fine-tuning job.
        """
        try:
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == job_id).first()
            
            if not job:
                return False
            
            # Delete model file if it exists
            if job.model_path and os.path.exists(job.model_path):
                try:
                    os.remove(job.model_path)
                except Exception as e:
                    logger.warning(f"Error deleting model file {job.model_path}: {str(e)}")
            
            # Delete job from database
            self.db.delete(job)
            self.db.commit()
            
            logger.info(f"Deleted fine-tuning job {job_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting fine-tuning job {job_id}: {str(e)}")
            raise e

    def chat_with_model(self, model_id: str, message: str, chat_mode: str, user_id: str) -> Dict[str, Any]:
        """        
        Chat with a fine-tuned model.
        """        
        try:
            start_time = time.time()            
            
            # Get the model details            
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == model_id).first()
            if not job or job.status != FinetuneStatus.COMPLETED:                
                raise ValueError(f"Model {model_id} not found or not ready")
                        
            # In a real system, you would use the model to generate a response
            # For demo purposes, we'll simulate this            
            time.sleep(random.uniform(0.5, 1.5))
                        
            if chat_mode == "model":
                response = f"This is a simulated response from the {job.model}-{job.type} model to your query: '{message}'"            
            elif chat_mode == "rag":
                response = f"This is a simulated RAG response using retrieval for your query: '{message}'"            
            else:  # both
                response = f"This is a combined response using both the {job.model}-{job.type} model and RAG for your query: '{message}'"            
            
            # Save to chat history            
            chat_entry = ChatHistory(
                user_id=user_id,                
                model_id=model_id,
                role="user",                
                content=message,
                chat_mode=chat_mode            
            )
            self.db.add(chat_entry)            
            
            response_entry = ChatHistory(                
                user_id=user_id,
                model_id=model_id,                
                role="assistant",
                content=response,                
                chat_mode=chat_mode
            )            
            self.db.add(response_entry)
            self.db.commit()            
            
            processing_time = time.time() - start_time            
            
            return {                
                "model_id": model_id,
                "response": response,                
                "chat_mode": chat_mode,
                "processing_time": processing_time,                
                "timestamp": datetime.now()
            }        
        except Exception as e:
            logger.error(f"Error chatting with model {model_id}: {str(e)}")            
            raise e

    def get_chat_history(self, model_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get chat history for a specific model and user.
        """
        try:
            history = self.db.query(ChatHistory).filter(
                ChatHistory.model_id == model_id,
                ChatHistory.user_id == user_id
            ).order_by(ChatHistory.timestamp).all()
            
            return [
                {
                    "role": entry.role,
                    "content": entry.content
                }
                for entry in history
            ]
        except Exception as e:
            logger.error(f"Error getting chat history for model {model_id}: {str(e)}")
            raise e

    def clear_chat_history(self, model_id: str, user_id: str) -> bool:
        """
        Clear chat history for a specific model and user.
        """
        try:
            self.db.query(ChatHistory).filter(
                ChatHistory.model_id == model_id,
                ChatHistory.user_id == user_id
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleared chat history for model {model_id} and user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing chat history for model {model_id}: {str(e)}")
            return False

    def compare_answers(self, model_id: str, question: str, user_id: str) -> Dict[str, Any]:
        """        
        Compare model and RAG answers for a question.
        """        
        try:
            start_time = time.time()            
            
            # Get the model details            
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == model_id).first()
            if not job or job.status != FinetuneStatus.COMPLETED:                
                raise ValueError(f"Model {model_id} not found or not ready")
                        
            # In a real system, you would use the model to generate responses
            # For demo purposes, we'll simulate this            
            time.sleep(random.uniform(0.5, 1.5))
                        
            model_answer = f"This is a simulated response from the {job.model}-{job.type} fine-tuned model for your question: '{question}'\n\nThe model has been specially trained to handle this type of query based on your fine-tuning dataset."
                        
            time.sleep(random.uniform(0.5, 1.0))
                        
            rag_answer = f"This is a simulated RAG (Retrieval-Augmented Generation) response for your question: '{question}'\n\nThe answer is generated by retrieving relevant information from your document database and using it to create this response."
                        
            processing_time = time.time() - start_time
                        
            return {
                "model_id": model_id,                
                "model_answer": model_answer,
                "rag_answer": rag_answer,
                "processing_time": processing_time,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error comparing answers for model {model_id}: {str(e)}")
            raise e

    def update_finetune_job(self, job_id: str, update_data: Dict[str, Any]) -> Optional[FinetuneResponse]:
        """
        Update a fine-tuning job with new values.
        
        Args:
            job_id: The ID of the job to update
            update_data: Dictionary containing fields to update
        
        Returns:
            Updated FinetuneResponse or None if job not found
        """
        try:
            job = self.db.query(FinetuneJob).filter(FinetuneJob.id == job_id).first()
            
            if not job:
                return None
            
            # Update fields if provided in update_data
            if "model" in update_data and update_data["model"] is not None:
                job.model = update_data["model"]
                
            if "type" in update_data and update_data["type"] is not None:
                job.type = update_data["type"]
                
            if "user_id" in update_data and update_data["user_id"] is not None:
                job.user_id = update_data["user_id"]
                
            if "status" in update_data and update_data["status"] is not None:
                job.status = update_data["status"]
                
            if "progress" in update_data and update_data["progress"] is not None:
                job.progress = update_data["progress"]
                
            if "message" in update_data and update_data["message"] is not None:
                job.message = update_data["message"]
                
            if "model_path" in update_data and update_data["model_path"] is not None:
                job.model_path = update_data["model_path"]
                
            if "description" in update_data and update_data["description"] is not None:
                job.description = update_data["description"]
                
            if "estimated_completion" in update_data and update_data["estimated_completion"] is not None:
                job.estimated_completion = update_data["estimated_completion"]
        
            # Always update the updated_at timestamp
            job.updated_at = datetime.now()
        
            self.db.commit()
            self.db.refresh(job)
        
            logger.info(f"Updated fine-tuning job: {job_id}")
        
            return FinetuneResponse(
                id=job.id,
                model=job.model,
                type=job.type,
                # job_ids=job.job_ids.split(",") if job.job_ids else [],
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                model_path=job.model_path,
                description=job.description,
                created_at=job.created_at,
                updated_at=job.updated_at,
                estimated_completion=job.estimated_completion
            )
        except Exception as e:
            logger.error(f"Error updating fine-tuning job {job_id}: {str(e)}")
            raise e
