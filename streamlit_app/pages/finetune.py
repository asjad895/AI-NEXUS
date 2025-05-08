import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import time
import requests
import json
from typing import List, Dict, Any, Optional

# API configuration
API_BASE_URL = "http://localhost:8000/api"

# Set page configuration
st.set_page_config(
    page_title="AI Model Fine-tuning Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stTabs {
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .card {
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }
    .card-title svg {
        margin-right: 10px;
    }
    .comparison-title {
        font-weight: bold;
        padding: 10px;
        border-radius: 5px 5px 0 0;
    }
    .job-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        # background-color: white;
    }
    .job-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .job-title {
        font-weight: bold;
        font-size: 1.1rem;
    }
    .status-running {
        color: #2196F3;
        background-color: rgba(33, 150, 243, 0.1);
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
    }
    .status-completed {
        color: #4CAF50;
        background-color: rgba(76, 175, 80, 0.1);
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
    }
    .status-failed {
        color: #F44336;
        background-color: rgba(244, 67, 54, 0.1);
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
    }
    .status-cancelled {
        color: #FF9800;
        background-color: rgba(255, 152, 0, 0.1);
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
    }
    .progress-container {
        margin-top: 10px;
    }
    .chat-messages {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        max-height: 400px;
        overflow-y: auto;
    }
    .message {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .user-message {
        # background-color: ;
        margin-left: 20%;
        margin-right: 5px;
    }
    .model-message {
        # background-color: #F5F5F5;
        margin-right: 20%;
        margin-left: 5px;
    }
    .empty-state {
        color: #757575;
        text-align: center;
        padding: 20px;
    }
    .comparison-answer {
        border: 1px solid #e0e0e0;
        border-radius: 0 0 5px 5px;
        padding: 15px;
        min-height: 200px;
        background-color: white;
    }
    
    /* Improve form styling */
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stSelectbox>div>div {
        padding: 2px 0;
    }
</style>
""", unsafe_allow_html=True)

# API functions
def api_request(method, endpoint, params=None, data=None):
    """Make an API request to the backend service."""
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            if params:
                response = requests.delete(url, params=params)
            else:
                response = requests.delete(url)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code in [200, 201, 202]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API Request Error: {str(e)}")
        return None

def get_finetune_jobs(user_id, status=None):
    """Get fine-tuning jobs for a user."""
    params = {"user_id": user_id}
    if status:
        params["status"] = status
    
    return api_request("GET", "finetune", params=params)

def create_finetune_job(model, finetune_type, job_ids, user_id, description=None):
    """Create a new fine-tuning job."""
    data = {
        "model": model,
        "type": finetune_type,
        "job_ids": job_ids.split(","),
        "user_id": user_id,
        "description": description
    }

    
    return api_request("POST", "finetune", data=data)

def get_finetune_job(job_id):
    """Get details of a specific fine-tuning job."""
    return api_request("GET", f"finetune/{job_id}")

def cancel_finetune_job(job_id):
    """Cancel a fine-tuning job."""
    return api_request("POST", f"finetune/{job_id}/cancel")

def delete_finetune_job(job_id):
    """Delete a fine-tuning job."""
    return api_request("DELETE", f"finetune/{job_id}")

def update_finetune_job(job_id, **kwargs):
    """Update a fine-tuning job with new values.
    
    Args:
        job_id: The ID of the job to update
        **kwargs: Fields to update (model, type, job_ids, user_id, status, 
                 progress, message, model_path, description, estimated_completion)
    """
    # Filter out None values
    data = {k: v for k, v in kwargs.items() if v is not None}
    
    # Convert job_ids to list if it's a string
    if "job_ids" in data and isinstance(data["job_ids"], str):
        data["job_ids"] = data["job_ids"].split(",")
    
    return api_request("PUT", f"finetune/{job_id}", data=data)

def chat_with_model(model_id, message, chat_mode, user_id):
    """Chat with a fine-tuned model."""
    data = {
        "model_id": model_id,
        "message": message,
        "chat_mode": chat_mode,
        "user_id": user_id
    }
    
    return api_request("POST", "chat", data=data)

def compare_answers(model_id, question, user_id):
    """Compare fine-tuned model and RAG answers."""
    data = {
        "model_id": model_id,
        "question": question,
        "user_id": user_id
    }
    
    return api_request("POST", "compare", data=data)

def get_chat_history(model_id, user_id):
    """Get chat history for a model and user."""
    params = {
        "model_id": model_id,
        "user_id": user_id
    }
    
    return api_request("GET", "chat/history", params=params)

def clear_chat_history(model_id, user_id):
    """Clear chat history for a model and user."""
    params = {
        "model_id": model_id,
        "user_id": user_id
    }
    
    return api_request("DELETE", "chat/history", params=params)

# Initialize session state for storing data
if 'user_id' not in st.session_state:
    st.session_state.user_id = None 

if 'jobs' not in st.session_state:
    st.session_state.jobs = []
    
if 'faq_jobs' not in st.session_state:
    st.session_state.faq_jobs = {"jobs": []}

if 'completed_models' not in st.session_state:
    st.session_state.completed_models = []
    
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Load jobs from API on page load
def load_jobs():
    jobs = get_finetune_jobs(st.session_state.user_id)
    if jobs:
        st.session_state.jobs = jobs
        st.session_state.completed_models = [
            job["id"] for job in jobs 
            # if job["status"] == "COMPLETED"
        ]

# Header
st.markdown("<h1 class='main-header'>AI Model Fine-tuning Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Fine-tune AI models with your data</p>", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Create Fine-tuning Job", 
    "Job Status", 
    "Chat with Model", 
    "Compare Answers"
])

# Tab 1: Create Fine-tuning Job
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 class='card-title'>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        Create New Fine-tuning Job
    </h2>
    """, unsafe_allow_html=True)
    
    # Form for creating a new fine-tuning job
    with st.form("create_job_form"):
        # Model selection
        model = st.selectbox(
            "Select Base Model",
            options=["llama3.3-3b_4bit", "mistral-7b", "gemma-7b", "phi-4-14b_4bit", "qwn3-14b_4bit"],
            help="Select the base model to fine-tune",
            key="model"
        )
        
        # Fine-tuning type
        finetune_type = st.selectbox(
            "Fine-tuning Type",
            options=["qa", "summarization", "classification", "embedding", "reasoning"],
            help="Select the type of fine-tuning to perform",
            key="finetune_type"
        )
        
        # Job IDs
        job_ids = st.text_input(
            "FAQ Job IDs",
            help="Comma-separated list of FAQ job IDs to use for fine-tuning",
            key="job_ids",
            value=st.session_state.get("job_ids", "")
        )
        
        # Description
        description = st.text_area(
            "Description",
            help="Optional description for this fine-tuning job",
            key="description"
        )
        
        submit_button = st.form_submit_button("Create Fine-tuning Job")
    
    if submit_button:
        if not job_ids:
            st.error("Please enter at least one FAQ job ID.")
        else:
            with st.spinner("Creating fine-tuning job..."):
                response = create_finetune_job(
                    model=model,
                    finetune_type=finetune_type,
                    job_ids=job_ids,
                    user_id=st.session_state.user_id,
                    description=description
                )
                
                if response:
                    st.success(f"Fine-tuning job created successfully with ID: {response['id']}")
                    
                    load_jobs()
                else:
                    st.error("Failed to create fine-tuning job.")
    
    # FAQ Job Selector
    st.markdown("<h3>Available FAQ Jobs</h3>", unsafe_allow_html=True)

    if len(st.session_state.faq_jobs.get("jobs", [])) == 0:
        st.markdown("<p class='empty-state'>Please enter user id to view FAQ jobs in sidebar</p>", unsafe_allow_html=True)

    if st.session_state.faq_jobs and not st.session_state.faq_jobs.get("jobs"):
        st.markdown(f"<p class='empty-state'>No FAQ jobs found for user {st.session_state.user_id}. Create FAQ jobs first.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='faq-jobs-list'>", unsafe_allow_html=True)
        
        for job in st.session_state.faq_jobs["jobs"]:
            if job["status"] == "Completed":
                # if st.button(f"Use Job {job['job_id']}", key=f"use_faq_{job['job_id']}"):
                #     # Pre-fill the job ID in the form
                #     if "job_ids" not in st.session_state:
                #         st.session_state.job_ids = job["job_id"]
                #     else:
                #         # If there's already a value, append the new job ID
                #         current_ids = st.session_state.job_ids.split(",") if st.session_state.job_ids else []
                #         if job["job_id"] not in current_ids:
                #             current_ids.append(job["job_id"])
                #             st.session_state.job_ids = ",".join(current_ids)
                    # st.rerun()
                
                st.markdown(f"""
                <div class='faq-job-item'>
                    <div class='faq-job-id'>ID: {job['job_id']}</div>
                    <div class='faq-job-status status-{job['status'].lower()}'>{job['status']}</div>
                    <div class='faq-job-date'>Created: {datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tab 2: Job Status
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 class='card-title'>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        Fine-tuning Job Status
    </h2>
    """, unsafe_allow_html=True)
    
    # Refresh button
    if st.button("Refresh Jobs"):
        with st.spinner("Loading jobs..."):
            load_jobs()
    
    # Display jobs
    if not st.session_state.jobs:
        st.markdown("<p class='empty-state'>No fine-tuning jobs found. Create a new job to get started.</p>", unsafe_allow_html=True)
    else:
        for job in st.session_state.jobs:
            st.markdown(f"""
            <div class='job-card'>
                <div class='job-header'>
                    <div class='job-title'>
                        <h3>{job["model"]} ({job["type"]})</h3>
                        <span class='job-id'>ID: {job["id"]}</span>
                    </div>
                    <div class='job-status status-{job["status"].lower()}'>
                        {job["status"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Description
            if job.get("description"):
                st.markdown(f"<p class='job-description'>{job['description']}</p>", unsafe_allow_html=True)
            
            # Progress bar for processing jobs
            if job["status"] == "PROCESSING":
                progress = job.get("progress", 0)
                st.progress(progress / 100)
                
                # Estimated completion time
                if job.get("estimated_completion"):
                    est_time = datetime.fromisoformat(job["estimated_completion"])
                    now = datetime.now()
                    if est_time > now:
                        time_left = est_time - now
                        hours, remainder = divmod(time_left.seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        st.markdown(f"<p class='completion-time'>Estimated completion in: {hours}h {minutes}m</p>", unsafe_allow_html=True)
            
            # Message
            if job.get("message"):
                st.markdown(f"<p class='job-message'>{job['message']}</p>", unsafe_allow_html=True)
            
            # Job details
            col1, col2 = st.columns(2)
            
            with col1:
                # Created/Updated timestamps
                if job.get("created_at"):
                    created_at = datetime.fromisoformat(job["created_at"])
                    st.markdown(f"<p class='job-timestamp'>Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
                
                if job.get("updated_at"):
                    updated_at = datetime.fromisoformat(job["updated_at"])
                    st.markdown(f"<p class='job-timestamp'>Updated: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
            
            with col2:
                # Action buttons
                if job["status"] == "PROCESSING" or job["status"] == "PENDING":
                    if st.button("Cancel Job", key=f"cancel_{job['id']}"):
                        with st.spinner("Cancelling job..."):
                            response = cancel_finetune_job(job["id"])
                            if response:
                                st.success(f"Job {job['id']} cancelled successfully.")
                                load_jobs()  # Refresh jobs list
                            else:
                                st.error(f"Failed to cancel job {job['id']}.")
                
                if st.button("Delete Job", key=f"delete_{job['id']}"):
                    with st.spinner("Deleting job..."):
                        response = delete_finetune_job(job["id"])
                        if response:
                            st.success(f"Job {job['id']} deleted successfully.")
                            load_jobs()  # Refresh jobs list
                        else:
                            st.error(f"Failed to delete job {job['id']}.")
                
                if st.button("Edit Job", key=f"edit_{job['id']}"):
                    # Set the job to edit in session state
                    st.session_state.editing_job_id = job["id"]
                    st.session_state.editing_job = job
                    st.rerun()

            # Check if we're editing a job
            if "editing_job_id" in st.session_state and st.session_state.editing_job_id:
                st.markdown("<div class='edit-job-form'>", unsafe_allow_html=True)
                st.markdown(f"<h3>Edit Job {st.session_state.editing_job_id}</h3>", unsafe_allow_html=True)
                
                # Create form for editing
                with st.form(f"{job['id']}_edit_job_form"):
                    # Get current values from the job
                    job = st.session_state.editing_job
                    
                    # Fields to ed               
                    description = st.text_area("Description", value=job.get("description", ""))
                    
                    status = st.selectbox(
                        "Status",
                        options=["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"],
                        index=["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"].index(job["status"])
                            if job["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"] else 0
                    )
                    
                    progress = st.slider("Progress", 0, 100, job.get("progress", 0))
                    
                    message = st.text_input("Message", value=job.get("message", ""))
                    
                    model_path = st.text_input("Model Path", value=job.get("model_path", ""))
                    
                    # Submit button
                    submit_button = st.form_submit_button("Update Job")
                    cancel_button = st.form_submit_button("Cancel")
                
                if submit_button:
                    with st.spinner("Updating job..."):
                        response = update_finetune_job(
                            job_id=st.session_state.editing_job_id,
                            model=model,
                            type=finetune_type,
                            job_ids=job_ids,
                            description=description,
                            status=status,
                            progress=progress,
                            message=message,
                            model_path=model_path
                        )
                        
                        if response:
                            st.success(f"Job {st.session_state.editing_job_id} updated successfully.")
                            # Clear editing state
                            del st.session_state.editing_job_id
                            del st.session_state.editing_job
                            # Refresh jobs list
                            load_jobs()
                            st.rerun()
                        else:
                            st.error(f"Failed to update job {st.session_state.editing_job_id}.")
                
                if cancel_button:
                    # Clear editing state
                    del st.session_state.editing_job_id
                    del st.session_state.editing_job
                    st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Model path for completed jobs
            if job["status"] == "COMPLETED" and job.get("model_path"):
                st.markdown(f"<p class='model-path'>Model path: {job['model_path']}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tab 3: Chat with Model
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 class='card-title'>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        Chat with Fine-tuned Model
    </h2>
    """, unsafe_allow_html=True)
    
    # Model selection
    if not st.session_state.completed_models:
        model_options = ["No models available"]
        selected_model = "No models available"
    else:
        model_options = st.session_state.completed_models
        selected_model = st.selectbox("Select Model", options=model_options, key="chat_model")
    
    # Chat mode selection
    chat_mode = st.radio(
        "Chat Mode",
        options=["model", "rag", "both"],
        format_func=lambda x: {
            "model": "Fine-tuned Model Only",
            "rag": "RAG Only",
            "both": "Combined (Model + RAG)"
        }[x],
        horizontal=True
    )
    
    # Load chat history when model is selected
    if selected_model != "No models available" and len(st.session_state.completed_models) > 0:
        # Check if we need to load chat history
        if "current_chat_model" not in st.session_state or st.session_state.current_chat_model != selected_model:
            with st.spinner("Loading chat history..."):
                history = get_chat_history(selected_model, st.session_state.user_id)
                if history:
                    st.session_state.chat_messages = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in history
                    ]
                else:
                    st.session_state.chat_messages = []
            
            st.session_state.current_chat_model = selected_model
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        if not st.session_state.completed_models or selected_model == "No models available":
            st.markdown("<div class='chat-messages'><p class='empty-state'>Select a model to start chatting.</p></div>", unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown("<div class='chat-messages'>", unsafe_allow_html=True)
                for message in st.session_state.chat_messages:
                    if message["role"] == "user":
                        st.markdown(f"<div class='message user-message'>{message['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='message model-message'>{message['content']}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat input
    if selected_model != "No models available" and len(st.session_state.completed_models) > 0:
        user_input = st.text_input("Type your message...", key="chat_input")
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            send_button = st.button("Send")
        with col2:
            if st.button("Clear Chat"):
                with st.spinner("Clearing chat history..."):
                    response = clear_chat_history(selected_model, st.session_state.user_id)
                    if response:
                        st.session_state.chat_messages = []
                        st.success("Chat history cleared.")
                    else:
                        st.error("Failed to clear chat history.")
        
        if send_button and user_input:
            # Add user message to UI immediately
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
            # Send to API
            with st.spinner("Model is thinking..."):
                response = chat_with_model(
                    model_id=selected_model,
                    message=user_input,
                    chat_mode=chat_mode,
                    user_id=st.session_state.user_id
                )
                
                if response:
                    # Add model response
                    st.session_state.chat_messages.append({"role": "assistant", "content": response["response"]})
                else:
                    st.error("Failed to get response from model.")
            
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tab 4: Compare Answers
with tab4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 class='card-title'>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
        </svg>
        Compare Fine-tuned vs RAG Answers
    </h2>
    """, unsafe_allow_html=True)
    
    # Select model
    if not st.session_state.completed_models:
        compare_model_options = ["No models available"]
    else:
        compare_model_options = st.session_state.completed_models
    
    compare_model = st.selectbox("Select Fine-tuned Model", options=compare_model_options, key="compare_model")
    
    # Question input
    compare_query = st.text_input("Your Question", key="compare_query", placeholder="Type your question...")
    
    # Compare button
    compare_button = st.button("Compare Answers", key="compare_button")
    
    # Display comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='comparison-title'>Fine-tuned Model Answer</div>", unsafe_allow_html=True)
        if compare_button and compare_query and compare_model != "No models available":
            with st.spinner("Generating comparison..."):
                response = compare_answers(
                    model_id=compare_model,
                    question=compare_query,
                    user_id=st.session_state.user_id
                )
                
                if response:
                    st.markdown(f"""
                    <div class='comparison-answer'>
                        {response["model_answer"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Failed to generate comparison.")
        else:
            st.markdown("<div class='comparison-answer'><p class='empty-state'>Ask a question to see the fine-tuned model answer.</p></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='comparison-title'>RAG Answer</div>", unsafe_allow_html=True)
        if compare_button and compare_query and compare_model != "No models available" and 'response' in locals():
            st.markdown(f"""
            <div class='comparison-answer'>
                {response["rag_answer"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='comparison-answer'><p class='empty-state'>Ask a question to see the RAG answer.</p></div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

if st.sidebar.button("Reset All Data"):
    with st.spinner("Resetting all data..."):
        
        # Clear session state
        st.session_state.jobs = []
        st.session_state.completed_models = []
        st.session_state.chat_messages = []
        st.session_state.user_id = None
        st.session_state.faq_jobs = {"jobs": []}
        
        st.sidebar.success("All data has been reset!")

# User authentication in sidebar
st.sidebar.title("User Authentication")

# Check if user is already logged in
if st.session_state.user_id:
    st.sidebar.success(f"Logged in as: {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.faq_jobs = {"jobs": []}
        st.session_state.jobs = []
        st.session_state.completed_models = []
        st.session_state.chat_messages = []
        st.rerun()
else:
    # Show login form
    with st.sidebar.form("login_form"):
        user_name = st.text_input("Enter user name", key="login_user_name")
        submit_button = st.form_submit_button("Login")
        
        if submit_button and user_name:
            st.session_state.user_id = user_name
            # Fetch FAQ jobs for this user
            try:
                response = api_request("GET", "faq/jobs", params={"user_id": user_name})
                if response:
                    st.write(response)
                    st.session_state.faq_jobs = response
                    # Also load finetune jobs
                    # load_jobs()
                    st.success(f"Logged in as: {user_name}")
                    st.rerun()
                else:
                    st.error("Failed to fetch user data")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                print(f"API Error: {str(e)}")

# Load jobs on initial page load
if len(st.session_state.jobs) == 0:
    st.sidebar.success("All data has been reset!")