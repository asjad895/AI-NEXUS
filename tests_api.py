"""
Unit tests for FAQ Pipeline API.
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from unittest.mock import patch
from MLETE.middleware.database import get_db, Base

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_faq_pipeline.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# @pytest.fixture(autouse=True)
# def setup_and_teardown():
#     # Setup test directories
#     os.makedirs("./test_uploads", exist_ok=True)
#     os.makedirs("./test_output", exist_ok=True)
    
#     # Create test file
#     with open("./test_uploads/test.docx", "w") as f:
#         f.write("""### **Section 1**

# 1. **What is this?**
# This is a test answer.

# 2. **How does it work?**
# It works like this.
# """)
    
#     yield
    
#     # Teardown - clean up test files
#     for path in ["./test_uploads/test.docx"]:
#         if os.path.exists(path):
#             os.remove(path)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

# @patch("main.process_faq_pipeline")
def test_process_faq(mock_process):
    mock_process.return_value = None
    
    response = client.post(
        "/api/faq/process",
        json={"file_path": ".\Unilife\General_unilife_faq.docx", "user_id": "test_user"}
    )
    
    assert response.status_code == 200
    assert "job_id" in response.json()
    assert response.json()["status"] == "Pending"

def test_get_job_status_not_found():
    response = client.get(f"/api/faq/job/{uuid.uuid4()}")
    assert response.status_code == 404

# @patch("main.process_faq_pipeline")
def test_create_and_get_job(mock_process):
    # First create a job
    mock_process.return_value = None
    
    create_response = client.post(
        "/api/faq/process",
        json={"file_path": ".\Unilife\General_unilife_faq.docx", "user_id": "test_user"}
    )
    
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]
    
    # Then get its status
    get_response = client.get(f"/api/faq/job/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == job_id
    assert get_response.json()["status"] == "Pending"

# def test_list_jobs():
#     response = client.get("/api/faq/jobs?user_id=test_user")
#     assert response.status_code == 200
#     assert "jobs" in response.json()
    
#     # Should have at least one job from previous test
#     assert len(response.json()["jobs"]) >= 1

# @patch("main.process_faq_pipeline")
def test_cancel_job(mock_process):
    # First create a job
    mock_process.return_value = None
    
    create_response = client.post(
        "/api/faq/process",
        json={"file_path": ".\Unilife\General_unilife_faq.docx", "user_id": "test_user"}
    )
    
    job_id = create_response.json()["job_id"]
    
    # Then cancel it
    cancel_response = client.delete(f"/api/faq/job/{job_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"
    
    # Verify it's cancelled
    get_response = client.get(f"/api/faq/job/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "Cancelled"