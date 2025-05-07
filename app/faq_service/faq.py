from abc import ABC, abstractmethod
from opik import Opik
from opik import track
import time
from typing import List, Tuple, Dict
import re
import os
import csv
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from middleware.models import FAQPipelineResponse,Status
from middleware.database import FAQJob, FAQEntry
from sqlalchemy.orm import Session
from middleware.logger import logger
os.environ["OPIK_API_KEY"] = "2Rofpa7vTaP91PL7rkNlp8KHK" 
os.environ["OPIK_WORKSPACE"] = "asjad12"
opik = Opik(project_name = 'faq_pipeline',api_key = '2Rofpa7vTaP91PL7rkNlp8KHK',workspace = 'asjad12')
class FAQService(ABC):
    def __init__(self, db: Session):
        self.db = db

    @track(name='extract_sections_and_faqs',project_name = 'faq_pipeline')
    def extract_sections_and_faqs(self, markdown_text: str) -> Tuple[List[str], List[dict]]:
        """
        Extract sections, questions, and answers from markdown text.
        """
        try:
            # Split the text into lines for processing
            lines = markdown_text.split('\n')
            
            sections = []
            current_section = None
            current_question = None
            current_answer = []
            faqs = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check for section header with ### prefix
                section_match = re.match(r'^### \*\*(.*?)(:?)\*\*$', line)
                
                # Check for section header without ### prefix (surrounded by empty lines)
                if not section_match and line.startswith('**') and line.endswith('**'):
                    # Check if this line is surrounded by empty lines
                    prev_line_empty = (i == 0 or not lines[i-1].strip())
                    next_line_empty = (i == len(lines)-1 or not lines[i+1].strip())
                    
                    if prev_line_empty and next_line_empty:
                        section_match = re.match(r'^\*\*(.*?)\*\*$', line)
                
                if section_match:
                    # Save the current section's data if we're moving to a new section
                    if current_section and current_question and current_answer:
                        faqs.append({
                            'section': current_section,
                            'question': current_question,
                            'answer': '\n'.join(current_answer).strip()
                        })
                        current_question = None
                        current_answer = []
                    
                    current_section = section_match.group(1).strip()
                    if current_section.startswith("Name: "):
                        current_section = current_section[6:].strip()  # Remove "Name: " prefix
                    sections.append(current_section)
                    
                # Check for numbered question
                elif re.match(r'^\d+\. \*\*(.*?)\*\*', line):
                    # If we already have a question in progress, save it first
                    if current_question and current_answer:
                        faqs.append({
                            'section': current_section,
                            'question': current_question,
                            'answer': '\n'.join(current_answer).strip()
                        })
                        current_answer = []
                    
                    # Extract the new question
                    question_match = re.match(r'^\d+\. \*\*(.*?)\*\*', line)
                    current_question = question_match.group(1).strip()
                    
                    # Extract any answer text on the same line after the question
                    remaining = line[question_match.end():].strip()
                    if remaining:
                        current_answer.append(remaining)
                
                # If not a section or question, it's part of the answer
                elif current_question is not None:
                    current_answer.append(line)
                
                i += 1
            
            # Don't forget to add the last FAQ
            if current_section and current_question and current_answer:
                faqs.append({
                    'section': current_section,
                    'question': current_question,
                    'answer': '\n'.join(current_answer).strip()
                })

            return sections, faqs
        except Exception as e:
            logger.error(f"Error extracting sections and FAQs: {str(e)}")
            raise e
    
    @track(name="create_faq_dataset",project_name='faq_pipeline')
    def create_faq_dataset(self,markdown_text: str, job_id: str, db_session: Session) -> FAQPipelineResponse:
        try:
            # Update job status to IN_PROGRESS
            job = db_session.query(FAQJob).filter(FAQJob.id == job_id).first()
            job.status = Status.IN_PROGRESS
            db_session.commit()
            
            # Extract the data
            sections, faqs = self.extract_sections_and_faqs(markdown_text)
            
            # Clean up the answers (remove extra whitespace), subsection, etc
            for i, faq in enumerate(faqs):
                # Remove extra whitespace
                faq['answer'] = re.sub(r'\n\s*\n+', '\n\n', faq['answer']).strip()
                
                answer = faq['answer']
                lines = answer.split('\n')
                faq['answer'] = '\n'.join([line for line in lines if line.strip() and not line.startswith('####')])
                subsection = re.search(r'####.*?\n', faq['answer'])
                if subsection:
                    logger.info(f"section: {sections[min(i-1, len(sections)-1)]}, subsection: {subsection.group()}")
                    faq['answer'] = faq['answer'][subsection.end():].strip()
            
            # Add unique IDs and create DataFrame
            for i, faq in enumerate(faqs):
                faq['id'] = i + 1
                
                # Create FAQEntry in the database
                entry = FAQEntry(
                    job_id=job_id,
                    section=faq['section'],
                    question=faq['question'],
                    answer=faq['answer']
                )
                db_session.add(entry)
            
            # Create output directory if it doesn't exist
            os.makedirs("./output", exist_ok=True)
            
            # Generate unique output path
            output_file = f"./output/{job_id}.csv"
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(faqs)
            cols = ['id', 'section', 'question', 'answer']
            df = df[cols]
            df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
            
            # Update job status to COMPLETED
            job.output_path = output_file
            job.status = Status.COMPLETED
            job.message = f"FAQ Dataset created successfully with {len(faqs)} FAQ entries from {len(sections)} unique sections."
            job.completed_at = datetime.now()
            db_session.commit()
            
            logger.info(f"Created CSV dataset '{output_file}' for job {job_id}")
            
            return FAQPipelineResponse(
                job_id=job_id,
                status=Status.COMPLETED,
                csv_path=output_file,
                message=f"FAQ Dataset created successfully with {len(faqs)} FAQ entries from {len(sections)} unique sections.",
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        except Exception as e:
            # Update job status to FAILED
            job = db_session.query(FAQJob).filter(FAQJob.id == job_id).first()
            job.status = Status.FAILED
            job.message = f"Error creating FAQ dataset: {str(e)}"
            db_session.commit()
            
            logger.error(f"Error creating FAQ dataset for job {job_id}: {str(e)}")
            return FAQPipelineResponse(
                job_id=job_id,
                status=Status.FAILED,
                message=f"Error creating FAQ dataset: {str(e)}",
                created_at=job.created_at,
                updated_at=job.updated_at
            )
    


    def get_markdown_text(self, file_path: str) -> str:
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert(file_path)
            print(result.markdown)
            return result.text_content
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise e

    @track(name="process_faq_pipeline",project_name='faq_pipeline')
    def process_faq_pipeline(self, job_id: str, file_path: str) -> FAQPipelineResponse:
        """
        Background task to process FAQ pipeline.
        """
        try:
            start_time = time.time()
            
            markdown_text = self.get_markdown_text(file_path)
            result = self.create_faq_dataset(markdown_text, job_id, self.db)
            
            from metrics import JOB_PROCESSING_TIME
            JOB_PROCESSING_TIME.labels(status=result.status).observe(time.time() - start_time)
            
            return result
        except Exception as e:
            logger.error(f"Error in background task for job {job_id}: {str(e)}")
            
            job = self.db.query(FAQJob).filter(FAQJob.id == job_id).first()
            if job:
                job.status = Status.FAILED
                job.message = f"Error processing FAQ pipeline: {str(e)}"
                self.db.commit()
            
                from metrics import JOB_PROCESSING_TIME
                JOB_PROCESSING_TIME.labels(status=Status.FAILED).observe(time.time() - start_time)
        finally:
            self.db.close()