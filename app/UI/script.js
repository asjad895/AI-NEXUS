// API Integration Configuration
const API_BASE_URL = 'http://localhost:8000/api';
// Set to false since we have a real backend
const USE_MOCK_DATA = false;

// Application state
let selectedFile = null;
let jobsData = [];
let activeJobPolling = null;
let currentUser = JSON.parse(localStorage.getItem('currentUser')) || { id: 'guest_user', name: 'Guest User' };

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    init();
});

function init() {
    // Set up event listeners
    setupEventListeners();
    
    // Display current user
    updateUserDisplay();
    
    // Load jobs data from API
    fetchJobs();
}

function updateUserDisplay() {
    const userDisplay = document.getElementById('currentUserDisplay');
    if (userDisplay) {
        userDisplay.textContent = currentUser.name;
    }
}

// User management functions
function showUserModal() {
    const modal = document.getElementById('userSettingsModal');
    const userIdInput = document.getElementById('userIdInput');
    const userNameInput = document.getElementById('userNameInput');
    
    userIdInput.value = currentUser.id;
    userNameInput.value = currentUser.name;
    
    modal.style.display = 'block';
}

function saveUserSettings() {
    const userIdInput = document.getElementById('userIdInput');
    const userNameInput = document.getElementById('userNameInput');
    
    const userId = userIdInput.value.trim();
    const userName = userNameInput.value.trim();
    
    if (!userId || !userName) {
        showToast('error', 'Invalid Input', 'User ID and Name cannot be empty');
        return;
    }
    
    // Update current user
    currentUser = { id: userId, name: userName };
    
    // Save to local storage
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    // Update display
    updateUserDisplay();
    
    // Close modal
    handleModalClose(document.getElementById('userSettingsModal'));
    
    // Refresh jobs
    fetchJobs();
    
    showToast('success', 'Settings Saved', 'User settings have been updated');
}

// Helper functions
function formatDateTime(date) {
    return new Date(date).toLocaleString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getStatusClass(status) {
    status = status.toLowerCase().replace(/\s+/g, '-');
    return `status-${status}`;
}

function showToast(type, title, message, duration = 3000) {
    const toast = document.getElementById('toast');
    const toastTitle = document.querySelector('.toast-title');
    const toastMessage = document.querySelector('.toast-message');
    const toastIcon = document.querySelector('.toast-icon i');
    
    toast.className = 'toast';
    if (type === 'success') {
        toast.classList.add('toast-success');
        toastIcon.className = 'fas fa-check-circle';
    } else if (type === 'error') {
        toast.classList.add('toast-error');
        toastIcon.className = 'fas fa-exclamation-circle';
    }
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// DOM Elements
const fileInput = document.getElementById('fileInput');
const dropArea = document.getElementById('dropArea');
const browseBtn = document.getElementById('browseBtn');
const uploadBtn = document.getElementById('uploadBtn');
const uploadSpinner = document.getElementById('uploadSpinner');
const uploadBtnText = document.getElementById('uploadBtnText');
const selectedFileInfo = document.getElementById('selectedFileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFileBtn = document.getElementById('removeFileBtn');
const jobsList = document.getElementById('jobsList');
const toastClose = document.getElementById('toastClose');
const resultsModal = document.getElementById('resultsModal');
const closeModal = document.getElementById('closeModal');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const resultsTableContainer = document.getElementById('resultsTableContainer');
const jsonOutput = document.getElementById('jsonOutput');
const rawOutput = document.getElementById('rawOutput');
const aiAssistantBtn = document.getElementById('aiAssistantBtn');
const aiAssistantPanel = document.getElementById('aiAssistantPanel');
const aiPanelClose = document.getElementById('aiPanelClose');
const aiMessages = document.getElementById('aiMessages');
const aiMessageInput = document.getElementById('aiMessageInput');
const aiSendBtn = document.getElementById('aiSendBtn');

// Setup event listeners
function setupEventListeners() {
    // File upload related
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const removeFileBtn = document.getElementById('removeFileBtn');
    
    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('dragover');
        }, false);
    });
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    }
    
    // Simplify the click handling - only make the browse button trigger file input
    browseBtn.addEventListener('click', function(e) {
        e.preventDefault();
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileSelection(this.files[0]);
        }
    });
    
    // Upload button click
    uploadBtn.addEventListener('click', handleFileUpload);
    
    // Remove file button click
    removeFileBtn.addEventListener('click', clearFileSelection);
    
    // Jobs list related
    const refreshJobsBtn = document.getElementById('refreshJobsBtn');
    refreshJobsBtn.addEventListener('click', fetchJobs);
    
    const statusFilter = document.getElementById('statusFilter');
    statusFilter.addEventListener('change', function() {
        renderJobsList();
    });
    
    // Modal related
    const closeModalButtons = document.querySelectorAll('.close-modal');
    closeModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            // Use the global closeModal function
            handleModalClose(modal);
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            handleModalClose(e.target);
        }
    });
    
    // Job details modal actions
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    downloadCsvBtn.addEventListener('click', function() {
        const jobId = this.getAttribute('data-job-id');
        downloadCSV(jobId);
    });
    
    const viewEntriesBtn = document.getElementById('viewEntriesBtn');
    viewEntriesBtn.addEventListener('click', function() {
        const jobId = this.getAttribute('data-job-id');
        openEntriesModal(jobId);
    });
    
    const cancelJobBtn = document.getElementById('cancelJobBtn');
    cancelJobBtn.addEventListener('click', function() {
        const jobId = this.getAttribute('data-job-id');
        cancelJob(jobId);
    });
    
    // Entries search and filter
    const entriesSearch = document.getElementById('entriesSearch');
    entriesSearch.addEventListener('input', filterEntries);
    
    const sectionFilter = document.getElementById('sectionFilter');
    sectionFilter.addEventListener('change', filterEntries);
    
    // User settings
    const userSettingsBtn = document.getElementById('userSettingsBtn');
    userSettingsBtn.addEventListener('click', showUserModal);
    
    const saveUserSettingsBtn = document.getElementById('saveUserSettingsBtn');
    saveUserSettingsBtn.addEventListener('click', saveUserSettings);
    
    // Job search
    const jobSearchBtn = document.getElementById('jobSearchBtn');
    jobSearchBtn.addEventListener('click', searchJobById);
    
    const jobSearchInput = document.getElementById('jobSearchInput');
    jobSearchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchJobById();
        }
    });
    
    // Copy job ID on click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('job-id')) {
            const jobId = e.target.getAttribute('title');
            copyJobId(jobId);
        }
    });
}

// File handling functions
let lastSelectedFile = null;
let lastSelectionTime = 0;

function handleFileSelection(file) {
    // Prevent duplicate file selection events within a short time period
    const now = Date.now();
    if (lastSelectedFile && lastSelectedFile.name === file.name && 
        lastSelectedFile.size === file.size && 
        (now - lastSelectionTime) < 1000) {
        console.log('Duplicate file selection detected and prevented');
        return;
    }
    
    // Update tracking variables
    lastSelectedFile = file;
    lastSelectionTime = now;
    
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('error', 'File Too Large', 'Please select a file smaller than 10MB.');
        return;
    }
    
    // Check file type
    const allowedTypes = ['.md', '.txt', '.docx'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showToast('error', 'Invalid File Type', 'Please select a .md, .txt, or .docx file.');
        return;
    }
    
    // Update UI
    selectedFile = file;
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('selectedFileInfo').style.display = 'block';
    document.getElementById('uploadBtn').disabled = false;
}

function clearFileSelection() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFileInfo').style.display = 'none';
    document.getElementById('uploadBtn').disabled = true;
}

async function handleFileUpload() {
    if (!selectedFile) return;
    
    // Show loading state
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadSpinner = document.getElementById('uploadSpinner');
    const uploadBtnText = document.getElementById('uploadBtnText');
    
    uploadBtn.disabled = true;
    uploadSpinner.style.display = 'inline-block';
    uploadBtnText.textContent = 'Processing...';
    
    try {
        // Create FormData and append the file
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('user_id', currentUser.id);
        
        // Make API request to upload the file
        const response = await fetch(`${API_BASE_URL}/faq/upload?user_id=${currentUser.id}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Update the jobs list
        fetchJobs();
        
        // Reset UI
        clearFileSelection();
        uploadSpinner.style.display = 'none';
        uploadBtnText.textContent = 'Upload & Process';
        
        // Show success message
        showToast('success', 'File Uploaded', 'Your file has been uploaded and is being processed.');
        
        // Open job details modal
        openJobDetailsModal(result.job_id);
    } catch (error) {
        console.error('Error uploading file:', error);
        uploadSpinner.style.display = 'none';
        uploadBtnText.textContent = 'Upload & Process';
        uploadBtn.disabled = false;
        showToast('error', 'Upload Failed', error.message || 'An error occurred during upload.');
    }
}

// API Interaction Functions
async function fetchJobs() {
    try {
        // Show loading state
        const jobsList = document.getElementById('jobsList');
        jobsList.innerHTML = '<div class="loading-spinner"></div>';
        
        // Fetch from the API
        const response = await fetch(`${API_BASE_URL}/faq/jobs?user_id=${currentUser.id}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch jobs: ${response.statusText}`);
        }
        
        const result = await response.json();
        jobsData = result.jobs || [];
        
        // Render the jobs list
        renderJobsList();
    } catch (error) {
        console.error('Error fetching jobs:', error);
        showToast('error', 'Failed to Load Jobs', error.message || 'An error occurred while loading jobs.');
        
        // Show error state
        const jobsList = document.getElementById('jobsList');
        jobsList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load jobs</p>
                <button class="btn btn-small" onclick="fetchJobs()">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>
            </div>
        `;
    }
}

async function fetchJobDetails(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/faq/job/${jobId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch job details: ${response.statusText}`);
        }
        
        const job = await response.json();
        
        // Update modal content
        updateJobDetailsModal(job);
        
        // Show the modal
        const modal = document.getElementById('jobDetailsModal');
        modal.style.display = 'block';
        
        // Start polling for job status updates
        startJobStatusPolling(jobId);
    } catch (error) {
        console.error('Error fetching job details:', error);
        showToast('error', 'Failed to Load Job Details', error.message || 'An error occurred while loading job details.');
    }
}

async function fetchFAQEntries(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/faq/jobs/${jobId}/entries`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch FAQ entries: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching FAQ entries:', error);
        showToast('error', 'Error', 'Failed to load FAQ entries. Please try again.');
        return [];
    }
}

async function downloadCSV(jobId) {
    try {
        // Create a link element
        const link = document.createElement('a');
        link.href = `${API_BASE_URL}/faq/download/${jobId}`;
        link.download = `faq_${jobId}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('Error downloading CSV:', error);
        showToast('error', 'Download Failed', error.message || 'An error occurred while downloading the CSV file.');
    }
}

// UI Rendering Functions
function renderJobsList() {
    const jobsList = document.getElementById('jobsList');
    const statusFilter = document.getElementById('statusFilter').value;
    
    // Filter jobs based on status
    let filteredJobs = jobsData;
    if (statusFilter !== 'all') {
        filteredJobs = jobsData.filter(job => job.status === statusFilter);
    }
    
    // Sort jobs by created_at (newest first)
    filteredJobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Clear the jobs list
    jobsList.innerHTML = '';
    
    // Check if there are any jobs
    if (filteredJobs.length === 0) {
        jobsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No jobs found</p>
                ${statusFilter !== 'all' ? '<p>Try changing the status filter</p>' : ''}
            </div>
        `;
        return;
    }
    
    // Create a table for better structure
    const table = document.createElement('table');
    table.className = 'jobs-table';
    
    // Add table header
    table.innerHTML = `
        <thead>
            <tr>
                <th>Job ID</th>
                <th>Status</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Message</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    
    const tableBody = table.querySelector('tbody');
    
    // Render each job
    filteredJobs.forEach(job => {
        const row = document.createElement('tr');
        row.className = `job-row ${getStatusClass(job.status)}`;
        
        row.innerHTML = `
            <td class="job-id" title="${job.job_id}">${job.job_id.substring(0, 8)}...</td>
            <td class="job-status">${job.status}</td>
            <td>${formatDateTime(job.created_at)}</td>
            <td>${formatDateTime(job.updated_at)}</td>
            <td class="job-message" title="${job.message || 'No message'}">${job.message || 'No message'}</td>
            <td class="job-actions">
                <button class="btn btn-small view-details-btn" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                ${job.status === 'Completed' ? `
                <button class="btn btn-small download-csv-btn" title="Download CSV">
                    <i class="fas fa-download"></i>
                </button>
                ` : ''}
                ${job.status === 'Pending' || job.status === 'In Progress' ? `
                <button class="btn btn-small cancel-job-btn" title="Cancel Job">
                    <i class="fas fa-times"></i>
                </button>
                ` : ''}
            </td>
        `;
        
        tableBody.appendChild(row);
        
        // Add event listeners to buttons
        const viewDetailsBtn = row.querySelector('.view-details-btn');
        viewDetailsBtn.addEventListener('click', () => openJobDetailsModal(job.job_id));
        
        const downloadCsvBtn = row.querySelector('.download-csv-btn');
        if (downloadCsvBtn) {
            downloadCsvBtn.addEventListener('click', () => downloadCSV(job.job_id));
        }
        
        const cancelJobBtn = row.querySelector('.cancel-job-btn');
        if (cancelJobBtn) {
            cancelJobBtn.addEventListener('click', () => cancelJob(job.job_id));
        }
    });
    
    jobsList.appendChild(table);
}

function openJobDetailsModal(jobId) {
    // Find the job in the jobsData array
    const job = jobsData.find(j => j.id === jobId);
    
    if (!job) {
        // If job not found, fetch it from the API
        fetchJobDetails(jobId);
        return;
    }
    
    // Update modal content
    updateJobDetailsModal(job);
    
    // Show the modal
    const modal = document.getElementById('jobDetailsModal');
    modal.style.display = 'block';
    
    // Start polling for job status updates
    startJobStatusPolling(jobId);
}

function updateJobDetailsModal(job) {
    // Update job details
    document.getElementById('detailJobId').textContent = job.job_id;
    document.getElementById('detailStatus').textContent = job.status;
    document.getElementById('detailCreated').textContent = formatDateTime(job.created_at);
    document.getElementById('detailUpdated').textContent = formatDateTime(job.updated_at);
    document.getElementById('detailMessage').textContent = job.message || 'No message';
    
    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressContainer = document.getElementById('progressContainer');
    
    if (job.status === 'Pending' || job.status === 'In Progress') {
        progressContainer.style.display = 'block';
        
        // Set progress based on status
        if (job.status === 'Pending') {
            progressBar.style.width = '10%';
            progressText.textContent = 'Waiting to start...';
        } else {
            progressBar.style.width = '50%';
            progressText.textContent = 'Processing...';
        }
    } else {
        progressContainer.style.display = 'none';
    }
    
    // Update action buttons
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const viewEntriesBtn = document.getElementById('viewEntriesBtn');
    const cancelJobBtn = document.getElementById('cancelJobBtn');
    
    downloadCsvBtn.setAttribute('data-job-id', job.job_id);
    viewEntriesBtn.setAttribute('data-job-id', job.job_id);
    cancelJobBtn.setAttribute('data-job-id', job.job_id);
    
    // Enable/disable buttons based on job status
    const isCompleted = job.status === 'Completed';
    downloadCsvBtn.disabled = !isCompleted;
    viewEntriesBtn.disabled = !isCompleted;
    
    // Hide cancel button if job is already completed or failed
    cancelJobBtn.style.display = (job.status === 'Completed' || job.status === 'Failed' || job.status === 'Cancelled') ? 'none' : 'inline-flex';
}

function startJobStatusPolling(jobId) {
    // Clear any existing polling
    if (activeJobPolling) {
        clearInterval(activeJobPolling);
    }
    
    // Start polling every 1 second
    activeJobPolling = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/faq/job/${jobId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch job status: ${response.statusText}`);
            }
            
            const job = await response.json();
            
            // Update the job in jobsData
            const index = jobsData.findIndex(j => j.id === jobId);
            if (index !== -1) {
                jobsData[index] = job;
            } else {
                jobsData.push(job);
            }
            
            // Update modal content
            updateJobDetailsModal(job);
            
            // If job is completed, failed, or cancelled, stop polling
            if (['Completed', 'Failed', 'Cancelled'].includes(job.status)) {
                clearInterval(activeJobPolling);
                activeJobPolling = null;
                
                // Show toast notification
                if (job.status === 'Completed') {
                    showToast('success', 'Job Completed', 'Your FAQ extraction job has been completed successfully.');
                } else if (job.status === 'Failed') {
                    showToast('error', 'Job Failed', job.message || 'Your FAQ extraction job has failed.');
                }
                
                // Refresh the jobs list
                renderJobsList();
            }
        } catch (error) {
            console.error('Error polling job status:', error);
            clearInterval(activeJobPolling);
            activeJobPolling = null;
        }
    }, 1000);
}

function handleModalClose(modal) {
    modal.style.display = 'none';
    
    // If it's the job details modal, stop polling
    if (modal.id === 'jobDetailsModal' && activeJobPolling) {
        clearInterval(activeJobPolling);
        activeJobPolling = null;
    }
}

async function openEntriesModal(jobId) {
    try {
        // Fetch entries from API
        const response = await fetch(`${API_BASE_URL}/faq/entries/${jobId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch entries: ${response.statusText}`);
        }
        
        const result = await response.json();
        const entries = result.entries || [];
        
        // Populate entries table
        populateEntriesTable(entries);
        
        // Show the modal
        const modal = document.getElementById('entriesModal');
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error fetching entries:', error);
        showToast('error', 'Failed to Load Entries', error.message || 'An error occurred while loading FAQ entries.');
    }
}

function populateEntriesTable(entries) {
    const tableBody = document.getElementById('entriesTableBody');
    const sectionFilter = document.getElementById('sectionFilter');
    
    // Clear the table
    tableBody.innerHTML = '';
    
    // Clear and populate section filter
    sectionFilter.innerHTML = '<option value="all">All Sections</option>';
    
    // Get unique sections
    const sections = [...new Set(entries.map(entry => entry.section))];
    
    // Add sections to filter
    sections.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        sectionFilter.appendChild(option);
    });
    
    // Populate table
    entries.forEach(entry => {
        const row = document.createElement('tr');
        row.setAttribute('data-section', entry.section);
        
        row.innerHTML = `
            <td>${entry.id}</td>
            <td>${entry.section}</td>
            <td>${entry.question}</td>
            <td>${entry.answer}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function filterEntries() {
    const searchTerm = document.getElementById('entriesSearch').value.toLowerCase();
    const sectionFilter = document.getElementById('sectionFilter').value;
    const rows = document.querySelectorAll('#entriesTableBody tr');
    
    rows.forEach(row => {
        const section = row.getAttribute('data-section');
        const text = row.textContent.toLowerCase();
        
        // Check if row matches both filters
        const matchesSearch = searchTerm === '' || text.includes(searchTerm);
        const matchesSection = sectionFilter === 'all' || section === sectionFilter;
        
        row.style.display = matchesSearch && matchesSection ? '' : 'none';
    });
}

async function cancelJob(jobId) {
    try {
        // Confirm cancellation
        if (!confirm('Are you sure you want to cancel this job?')) {
            return;
        }
        
        // In a real app, you would send a request to cancel the job
        // For now, we'll simulate by removing the job from jobsData
        const index = jobsData.findIndex(job => job.id === jobId);
        if (index !== -1) {
            jobsData.splice(index, 1);
            renderJobsList();
            showToast('success', 'Job Cancelled', 'Your job has been cancelled.');
        }
    } catch (error) {
        console.error('Error cancelling job:', error);
        showToast('error', 'Failed to Cancel Job', error.message || 'An error occurred while cancelling the job.');
    }
}

// AI Assistant Functions
function sendAIMessage() {
    const message = aiMessageInput.value.trim();
    if (!message) return;
    
    // Add user message to the chat
    addAIMessage('user', message);
    
    // Clear input
    aiMessageInput.value = '';
    
    // In a real app, you would send this to an API
    // For now, simulate a response
    setTimeout(() => {
        // This would be replaced with actual API call
        fetchAIResponse(message)
            .then(response => {
                addAIMessage('assistant', response);
            })
            .catch(error => {
                console.error('Error fetching AI response:', error);
                addAIMessage('assistant', 'Sorry, I encountered an error processing your request.');
            });
    }, 500);
}

async function fetchAIResponse(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_id: currentUser.id
            })
        });
        
        if (!response.ok) {
            throw new Error(`AI request failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        return result.response;
    } catch (error) {
        console.error('Error with AI request:', error);
        return 'Sorry, I encountered an error processing your request.';
    }
}

function addAIMessage(type, content) {
    const messageElement = document.createElement('div');
    messageElement.className = `ai-message ${type}-message`;
    
    messageElement.innerHTML = `
        <div class="ai-message-content">
            ${content}
        </div>
    `;
    
    aiMessages.appendChild(messageElement);
    
    // Scroll to the bottom
    aiMessages.scrollTop = aiMessages.scrollHeight;
}

// Add a function to copy job ID to clipboard
function copyJobId(jobId) {
    navigator.clipboard.writeText(jobId).then(() => {
        showToast('success', 'Copied', 'Job ID copied to clipboard');
    }).catch(err => {
        console.error('Could not copy text: ', err);
        showToast('error', 'Copy Failed', 'Could not copy job ID');
    });
}

// Add a function to search for a specific job by ID
function searchJobById() {
    const searchInput = document.getElementById('jobSearchInput');
    const jobId = searchInput.value.trim();
    
    if (!jobId) {
        showToast('error', 'Invalid Input', 'Please enter a job ID');
        return;
    }
    
    // First check if the job is in our local data
    const job = jobsData.find(j => j.job_id === jobId);
    
    if (job) {
        openJobDetailsModal(jobId);
    } else {
        // If not found locally, try to fetch from API
        fetchJobDetails(jobId);
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init);
