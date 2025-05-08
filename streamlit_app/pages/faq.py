import streamlit as st
import pandas as pd
import requests
import os
import time
import uuid
from datetime import datetime
import io

# API configuration
API_BASE_URL = "http://localhost:8000/api"

# Set page configuration
st.set_page_config(
    page_title="FAQ Pipeline",
    page_icon="❓",
    layout="wide",
    initial_sidebar_state="expanded"
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
        color: #666;
    }
    .card {
        background-color: white;
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .upload-container {
        border: 2px dashed #ccc;
        border-radius: 5px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
    }
    .status-Pending {
        color: #f39c12;
    }
    .status-In.Progress {
        color: #3498db;
    }
    .status-Completed {
        color: #2ecc71;
    }
    .status-Failed {
        color: #e74c3c;
    }
    .status-Cancelled {
        color: #95a5a6;
    }
    .job-card {
        border: 1px solid #eee;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .job-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .job-id {
        font-family: monospace;
        color: #666;
    }
    .empty-state {
        text-align: center;
        padding: 30px;
        color: #666;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'jobs' not in st.session_state:
    st.session_state.jobs = []

if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None

if 'entries' not in st.session_state:
    st.session_state.entries = []

if 'polling_job_id' not in st.session_state:
    st.session_state.polling_job_id = None

# API functions
def api_request(method, endpoint, params=None, data=None, files=None):
    """Make an API request to the backend service."""
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method.lower() == "get":
            response = requests.get(url, params=params)
        elif method.lower() == "post":
            response = requests.post(url, params=params, json=data, files=files)
        elif method.lower() == "delete":
            response = requests.delete(url, params=params)
        else:
            st.error(f"Unsupported method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API Request Error: {str(e)}")
        return None

def fetch_jobs():
    """Fetch jobs from the API."""
    if not st.session_state.user_id:
        return []
    
    response = api_request("GET", f"faq/jobs", params={"user_id": st.session_state.user_id})
    if response and "jobs" in response:
        # print(response["jobs"])
        return response["jobs"]
    return []

def fetch_job_details(job_id):
    """Fetch details for a specific job."""
    response = api_request("GET", f"faq/job/{job_id}")
    return response

def fetch_entries(job_id):
    """Fetch FAQ entries for a job."""
    response = api_request("GET", f"faq/entries/{job_id}")
    if response and "entries" in response:
        return response["entries"]
    return []

def cancel_job(job_id):
    """Cancel a job."""
    response = api_request("POST", f"faq/job/{job_id}/cancel")
    return response

def upload_file(file, user_id):
    """Upload a file for processing."""
    files = {"file": (file.name, file, "application/octet-stream")}
    response = api_request("POST", "faq/upload", params={"user_id": user_id}, files=files)
    return response

# UI Components
def render_header():
    """Render the page header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='main-header'>FAQ Pipeline</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Extract FAQs from documents automatically</p>", unsafe_allow_html=True)
    with col2:
        if st.session_state.user_id:
            st.markdown(f"<p style='text-align: right; padding-top: 10px;'>Welcome, <b>{st.session_state.user_id}</b></p>", unsafe_allow_html=True)

def render_upload_section():
    """Render the file upload section."""
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='card-title'>Upload Document</h2>", unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["md", "txt", "docx"],
        help="Supports .md, .txt, .docx files up to 10MB",
        key="file_uploader"
    )
    
    # Show file info if a file is selected
    if uploaded_file:
        file_size = len(uploaded_file.getvalue())
        file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"
        
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <strong>Selected File:</strong> {uploaded_file.name}
            <span style="margin-left: 10px; color: #888; font-size: 14px;">{file_size_str}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Upload button
        if st.button("Upload & Process", key="upload_btn"):
            if not st.session_state.user_id:
                st.error("Please enter a user ID in the sidebar first.")
            else:
                with st.spinner("Uploading and processing file..."):
                    response = upload_file(uploaded_file, st.session_state.user_id)
                    if response and "job_id" in response:
                        st.success(f"File uploaded successfully! Job ID: {response['job_id']}")
                        # Refresh jobs list
                        st.session_state.jobs = fetch_jobs()
                        # Set the new job as selected
                        st.session_state.selected_job = response["job_id"]
                        # Start polling for this job
                        st.session_state.polling_job_id = response["job_id"]
                        # Rerun to update UI
                        st.rerun()
                    else:
                        st.error("Failed to upload file. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_jobs_list():
    """Render the jobs list section."""
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Header with refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 class='card-title'>Processing Jobs</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.session_state.jobs = fetch_jobs()
            st.rerun()
    
    # Status filter
    status_options = ["All", "Pending", "In Progress", "Completed", "Failed", "Cancelled"]
    status_filter = st.selectbox("Filter by status:", status_options, key="status_filter")
    
    # Search box
    job_search = st.text_input("Search by Job ID:", key="job_search")
    
    # Filter jobs
    filtered_jobs = st.session_state.jobs
    if status_filter != "All":
        filtered_jobs = [job for job in filtered_jobs if job["status"] == status_filter]
    
    if job_search:
        filtered_jobs = [job for job in filtered_jobs if job_search.lower() in job["job_id"].lower()]
    
    # Sort jobs by created_at (newest first)
    filtered_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Display jobs
    if not filtered_jobs:
        st.markdown("<div class='empty-state'>No jobs found</div>", unsafe_allow_html=True)
    else:
        for job in filtered_jobs:
            job_id = job["job_id"]
            status = job["status"]
            created_at = datetime.fromisoformat(job["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Job card
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class='job-card'>
                        <div class='job-header'>
                            <div>
                                <span class='job-id' title='{job_id}'>{job_id}</span>
                                <span class='status-{status.replace(" ", ".")}'>• {status}</span>
                            </div>
                            <div>{created_at}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("View Details", key=f"view_{job_id}"):
                        st.session_state.selected_job = job_id
                        st.rerun()
                with col3:
                    if status not in ["Completed", "Failed", "Cancelled"]:
                        if st.button("Cancel", key=f"cancel_{job_id}"):
                            with st.spinner("Cancelling job..."):
                                response = cancel_job(job_id)
                                if response:
                                    st.success("Job cancelled successfully!")
                                    # Refresh jobs list
                                    st.session_state.jobs = fetch_jobs()
                                    st.rerun()
                                else:
                                    st.error("Failed to cancel job. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_job_details():
    """Render job details if a job is selected."""
    if not st.session_state.selected_job:
        return
    
    # Fetch job details
    job = fetch_job_details(st.session_state.selected_job)
    if not job:
        st.error(f"Failed to load details for job {st.session_state.selected_job}")
        return
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Header with close button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 class='card-title'>Job Details</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("Close", key="close_details"):
            st.session_state.selected_job = None
            st.session_state.polling_job_id = None
            st.rerun()
    
    # Job info
    st.markdown(f"""
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;'>
        <div>
            <strong>Job ID:</strong> {job["job_id"]}
        </div>
        <div>
            <strong>Status:</strong> <span class='status-{job["status"].replace(" ", ".")}'>• {job["status"]}</span>
        </div>
        <div>
            <strong>Created:</strong> {datetime.fromisoformat(job["created_at"]).strftime("%Y-%m-%d %H:%M:%S")}
        </div>
        <div>
            <strong>Updated:</strong> {datetime.fromisoformat(job["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")}
        </div>
        <div style='grid-column: span 2;'>
            <strong>Message:</strong> {job["message"]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar for in-progress jobs
    if job["status"] in ["Pending", "In Progress"]:
        progress = 0
        if job["status"] == "In Progress":
            progress = 0.5  # Simplified - in a real app, you'd get actual progress
        
        st.progress(progress, text="Processing...")
        
        # Set up polling for this job
        if st.session_state.polling_job_id != job["job_id"]:
            st.session_state.polling_job_id = job["job_id"]
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        download_disabled = job["status"] != "Completed"
        st.button("Download CSV", disabled=download_disabled, key="download_csv", 
                 on_click=lambda: download_csv(job["job_id"]) if not download_disabled else None)
    
    with col2:
        view_disabled = job["status"] != "Completed"
        if st.button("View Entries", disabled=view_disabled, key="view_entries"):
            st.session_state.entries = fetch_entries(job["job_id"])
            st.rerun()
    
    with col3:
        cancel_disabled = job["status"] in ["Completed", "Failed", "Cancelled"]
        if st.button("Cancel Job", disabled=cancel_disabled, key="cancel_job"):
            with st.spinner("Cancelling job..."):
                response = cancel_job(job["job_id"])
                if response:
                    st.success("Job cancelled successfully!")
                    # Refresh job details
                    st.session_state.jobs = fetch_jobs()
                    st.rerun()
                else:
                    st.error("Failed to cancel job. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_entries_table():
    """Render the FAQ entries table if entries are loaded."""
    if not st.session_state.entries:
        return
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Header with close button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 class='card-title'>FAQ Entries</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("Close", key="close_entries"):
            st.session_state.entries = []
            st.rerun()
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search entries:", key="entries_search")
    with col2:
        sections = ["All Sections"] + list(set(entry["section"] for entry in st.session_state.entries))
        section_filter = st.selectbox("Filter by section:", sections, key="section_filter")
    
    # Filter entries
    filtered_entries = st.session_state.entries
    if search_term:
        filtered_entries = [
            entry for entry in filtered_entries 
            if search_term.lower() in entry["question"].lower() or search_term.lower() in entry["answer"].lower()
        ]
    
    if section_filter != "All Sections":
        filtered_entries = [entry for entry in filtered_entries if entry["section"] == section_filter]
    
    # Display entries as a table
    if not filtered_entries:
        st.markdown("<div class='empty-state'>No entries found</div>", unsafe_allow_html=True)
    else:
        # Convert to DataFrame for better display
        df = pd.DataFrame(filtered_entries)
        st.dataframe(
            df[["id", "section", "question", "answer"]],
            use_container_width=True,
            height=400
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

def download_csv(job_id):
    """Download CSV for a job."""
    try:
        response = requests.get(f"{API_BASE_URL}/faq/download/{job_id}")
        if response.status_code == 200:
            # Create a download button
            st.download_button(
                label="Download CSV",
                data=response.content,
                file_name=f"faq_{job_id}.csv",
                mime="text/csv",
                key="download_button"
            )
            st.success("CSV downloaded successfully!")
        else:
            st.error(f"Failed to download CSV: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error downloading CSV: {str(e)}")

def poll_job_status():
    """Poll for job status updates."""
    if st.session_state.polling_job_id:
        job_id = st.session_state.polling_job_id
        job = fetch_job_details(job_id)
        
        if job and job["status"] in ["Completed", "Failed", "Cancelled"]:
            # Job is done, stop polling
            st.session_state.polling_job_id = None
            # Refresh jobs list
            st.session_state.jobs = fetch_jobs()
            # Show notification
            if job["status"] == "Completed":
                st.success("Job completed successfully!")
            elif job["status"] == "Failed":
                st.error(f"Job failed: {job['message']}")
            else:
                st.warning("Job was cancelled.")
            
            # Rerun to update UI
            st.rerun()

# Sidebar for user settings
def render_sidebar():
    """Render the sidebar with user settings."""
    st.sidebar.title("User Settings")
    
    if st.session_state.user_id:
        st.sidebar.success(f"Logged in as: {st.session_state.user_id}")
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.jobs = []
            st.session_state.selected_job = None
            st.session_state.entries = []
            st.session_state.polling_job_id = None
            st.rerun()
    else:
        with st.sidebar.form("login_form"):
            user_id = st.text_input("Enter User ID:", key="login_user_id")
            submit = st.form_submit_button("Login")
            
            if submit and user_id:
                st.session_state.user_id = user_id
                # Fetch jobs for this user
                st.session_state.jobs = fetch_jobs()
                st.rerun()

    # Navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("- [Home](/)") 
    st.sidebar.markdown("- [FAQ Pipeline](/faq)")
    st.sidebar.markdown("- [Fine-tuning](/finetune)")
    st.sidebar.markdown("- [Smart Agents](/smart_agent)")
    
    # About section
    st.sidebar.title("About")
    st.sidebar.info(
        """
        This app allows you to extract FAQs from documents automatically.
        Upload a document and the system will identify questions and answers.
        """
    )

# Main app
def main():
    """Main application function."""
    # Render sidebar
    render_sidebar()
    
    # Check if user is logged in
    if not st.session_state.user_id:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.warning("Please login in the sidebar to use the FAQ Pipeline.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Render header
    render_header()
    
    # Poll for job status updates
    poll_job_status()
    
    # Render upload section
    render_upload_section()
    
    # Render jobs list
    render_jobs_list()
    
    # Render job details if a job is selected
    if st.session_state.selected_job:
        render_job_details()
    
    # Render entries table if entries are loaded
    if st.session_state.entries:
        render_entries_table()

if __name__ == "__main__":
    main()