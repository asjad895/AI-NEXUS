// Global state
const state = {
    jobs: [],
    completedModels: []
};

// Generate a unique ID for jobs
function generateUniqueId() {
    return 'job-' + Math.random().toString(36).substring(2, 11);
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Tab Navigation
    const tabHeaders = document.querySelectorAll('.tab-header');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const tabId = header.getAttribute('data-tab');
            
            // Update active tab header
            tabHeaders.forEach(h => h.classList.remove('active'));
            header.classList.add('active');
            
            // Show selected tab content
            tabContents.forEach(content => {
                if (content.id === tabId) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        });
    });
    
    // Form submission
    const finetuneForm = document.getElementById('finetune-form');
    finetuneForm.addEventListener('submit', submitFinetuningJob);
    
    // Chat functionality
    const sendChatButton = document.getElementById('send-chat');
    sendChatButton.addEventListener('click', sendChatMessage);
    
    // Press Enter to send chat message
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Compare functionality
    const compareButton = document.getElementById('compare-button');
    compareButton.addEventListener('click', compareAnswers);
    
    // Press Enter to trigger comparison
    const compareQuery = document.getElementById('compare-query');
    compareQuery.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            compareAnswers();
        }
    });
    
    // Load saved jobs from local storage
    loadJobsFromLocalStorage();
    
    // Check for status updates for active jobs
    setInterval(checkJobStatuses, 60000); // Check every minute
});

// Load jobs from local storage
function loadJobsFromLocalStorage() {
    const savedJobs = localStorage.getItem('finetuning-jobs');
    if (savedJobs) {
        state.jobs = JSON.parse(savedJobs);
        updateJobStatusUI();
        
        // Also load completed models
        const completedJobs = state.jobs.filter(job => job.status === 'COMPLETED' && job.model_path);
        state.completedModels = completedJobs.map(job => ({
            id: job.id,
            name: `${job.model} (${job.type})`,
            model_path: job.model_path
        }));
        
        updateModelSelectOptions();
    }
}

// Save jobs to local storage
function saveJobsToLocalStorage() {
    localStorage.setItem('finetuning-jobs', JSON.stringify(state.jobs));
}

// Submit new fine-tuning job
async function submitFinetuningJob(event) {
    event.preventDefault();
    
    const jobIdsInput = document.getElementById('job-ids').value;
    const model = document.getElementById('model-select').value;
    const type = document.getElementById('type-select').value;
    
    // Parse job IDs
    const jobIds = jobIdsInput.split(',').map(id => id.trim()).filter(id => id);
    
    if (jobIds.length === 0) {
        alert('Please enter at least one job ID');
        return;
    }
    
    try {
        // Generate a unique ID for this fine-tuning job
        const jobId = generateUniqueId();
        
        // Create job in local state with initial PENDING status
        const job = {
            id: jobId,
            jobIds: jobIds,
            model: model,
            type: type,
            status: 'PENDING',
            message: 'Job submitted',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        
        state.jobs.push(job);
        saveJobsToLocalStorage();
        
        // In a real application, you would make an API request here
        // For example:
        /*
        const response = await fetch('/api/finetune', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                jobIds: jobIds,
                model: model,
                type: type
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit fine-tuning job');
        }
        
        const result = await response.json();
        */
        
        // Simulate API call for demo purposes
        setTimeout(() => {
            // Simulate job started processing
            const jobIndex = state.jobs.findIndex(j => j.id === jobId);
            if (jobIndex !== -1) {
                state.jobs[jobIndex].status = 'PROCESSING';
                state.jobs[jobIndex].message = 'Fine-tuning in progress';
                state.jobs[jobIndex].updated_at = new Date().toISOString();
                saveJobsToLocalStorage();
                updateJobStatusUI();
            }
            
            // Simulate job completion after delay
            setTimeout(() => {
                const jobIndex = state.jobs.findIndex(j => j.id === jobId);
                if (jobIndex !== -1) {
                    state.jobs[jobIndex].status = 'COMPLETED';
                    state.jobs[jobIndex].message = 'Fine-tuning completed successfully';
                    state.jobs[jobIndex].updated_at = new Date().toISOString();
                    state.jobs[jobIndex].model_path = `/models/${model}-${type}-${jobId}`;
                    
                    // Add to completed models
                    state.completedModels.push({
                        id: jobId,
                        name: `${model} (${type})`,
                        model_path: `/models/${model}-${type}-${jobId}`
                    });
                    
                    saveJobsToLocalStorage();
                    updateJobStatusUI();
                    updateModelSelectOptions();
                }
            }, 10000); // Complete after 10 seconds for demo
        }, 2000); // Start processing after 2 seconds for demo
        
        // Update UI
        updateJobStatusUI();
        
        // Show the job status tab
        document.querySelector('[data-tab="job-status"]').click();
        
        // Reset form
        finetuneForm.reset();
        
    } catch (error) {
        console.error('Error submitting fine-tuning job:', error);
        alert('Failed to submit fine-tuning job: ' + error.message);
    }
}

// Check status of active jobs
async function checkJobStatuses() {
    const activeJobs = state.jobs.filter(job => 
        job.status === 'PENDING' || job.status === 'PROCESSING'
    );
    
    // In a real application, you would make actual API requests here
    // For demo purposes, we'll simulate job progression
    for (const job of activeJobs) {
        if (job.status === 'PENDING') {
            // Move pending jobs to processing
            const jobIndex = state.jobs.findIndex(j => j.id === job.id);
            if (jobIndex !== -1) {
                state.jobs[jobIndex].status = 'PROCESSING';
                state.jobs[jobIndex].message = 'Fine-tuning in progress';
                state.jobs[jobIndex].updated_at = new Date().toISOString();
            }
        } else if (job.status === 'PROCESSING') {
            // Randomly complete some processing jobs
            if (Math.random() > 0.5) {
                const jobIndex = state.jobs.findIndex(j => j.id === job.id);
                if (jobIndex !== -1) {
                    state.jobs[jobIndex].status = 'COMPLETED';
                    state.jobs[jobIndex].message = 'Fine-tuning completed successfully';
                    state.jobs[jobIndex].updated_at = new Date().toISOString();
                    state.jobs[jobIndex].model_path = `/models/${job.model}-${job.type}-${job.id}`;
                    
                    // Add to completed models
                    if (!state.completedModels.some(m => m.id === job.id)) {
                        state.completedModels.push({
                            id: job.id,
                            name: `${job.model} (${job.type})`,
                            model_path: `/models/${job.model}-${job.type}-${job.id}`
                        });
                    }
                }
            }
        }
    }
    
    saveJobsToLocalStorage();
    updateJobStatusUI();
    updateModelSelectOptions();
}

// Update the job status UI
function updateJobStatusUI() {
    const jobStatusContainer = document.getElementById('job-status-container');
    
    if (state.jobs.length === 0) {
        jobStatusContainer.innerHTML = '<p class="empty-state">No fine-tuning jobs found. Create a new job to get started.</p>';
        return;
    }
    
    let html = '';
    
    state.jobs.forEach(job => {
        let statusClass = '';
        switch (job.status) {
            case 'PENDING': statusClass = 'status-pending'; break;
            case 'PROCESSING': statusClass = 'status-processing'; break;
            case 'COMPLETED': statusClass = 'status-completed'; break;
            case 'FAILED': statusClass = 'status-failed'; break;
        }
        
        html += `
            <div class="job-item">
                <div>
                    <div class="job-id">Job #${job.id}</div>
                    <div class="job-info">
                        ${job.model} | ${job.type} | Created: ${formatDate(job.created_at)}
                    </div>
                </div>
                <div class="job-details">
                    <span class="status-badge ${statusClass}">${job.status}</span>
                    ${job.status === 'COMPLETED' ? 
                        `<button class="btn btn-primary" onclick="openChatForModel('${job.id}')">Chat</button>` : 
                        ''}
                </div>
            </div>
        `;
    });
    
    jobStatusContainer.innerHTML = html;
}

// Update model select options
function updateModelSelectOptions() {
    const chatModelSelect = document.getElementById('chat-model-select');
    const compareModelSelect = document.getElementById('compare-model-select');
    
    if (state.completedModels.length === 0) {
        chatModelSelect.innerHTML = '<option value="">No models available</option>';
        compareModelSelect.innerHTML = '<option value="">No models available</option>';
        return;
    }
    
    let chatOptionsHtml = '';
    let compareOptionsHtml = '';
    
    state.completedModels.forEach(model => {
        const optionHtml = `<option value="${model.id}">${model.name}</option>`;
        chatOptionsHtml += optionHtml;
        compareOptionsHtml += optionHtml;
    });
    
    chatModelSelect.innerHTML = chatOptionsHtml;
    compareModelSelect.innerHTML = compareOptionsHtml;
}

// Open chat tab for a specific model
function openChatForModel(modelId) {
    // Switch to chat tab
    document.querySelector('[data-tab="chat-model"]').click();
    
    // Select the model in the dropdown
    const chatModelSelect = document.getElementById('chat-model-select');
    chatModelSelect.value = modelId;
    
    // Clear previous chat messages
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<p class="system-message">New conversation started with model. Ask a question to begin.</p>';
}

// Send chat message
async function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const query = chatInput.value.trim();
    const modelId = document.getElementById('chat-model-select').value;
    const mode = document.querySelector('input[name="chat-mode"]:checked').value;
    
    if (!query) return;
    if (!modelId) {
        alert('Please select a model first');
        return;
    }
    
    try {
        // Add user message to chat
        addMessageToChat('user', query);
        
        // Clear input
        chatInput.value = '';
        
        // In a real application, you would make an API request here
        // For example:
        /*
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                modelId: modelId,
                mode: mode
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response from model');
        }
        
        const result = await response.json();
        addMessageToChat('model', result.response);
        */
        
        // Simulate API response for demo purposes
        setTimeout(() => {
            // Generate different responses based on mode
            let modelResponse;
            
            if (mode === 'model' || mode === 'both') {
                // Generate fine-tuned model response
                const selectedModel = state.completedModels.find(model => model.id === modelId);
                const modelType = selectedModel.name.split('(')[1].replace(')', '').trim();
                
                let finetunedResponse;
                switch(modelType) {
                    case 'qa':
                        finetunedResponse = `This is a simulated response from the fine-tuned QA model for: "${query}"`;
                        break;
                    case 'reasoning':
                        finetunedResponse = `Let me think about "${query}"... \n\nAfter analyzing the question, I can provide this detailed reasoning: The answer depends on several factors including context, domain knowledge, and specific constraints.`;
                        break;
                    case 'summarization':
                        finetunedResponse = `Summary of your query: "${query}" - This appears to be a question about ${query.split(' ').slice(0, 3).join(' ')}... with potential implications for further discussion.`;
                        break;
                    default:
                        finetunedResponse = `Fine-tuned model response to: "${query}" - I've been specifically trained to handle this type of query based on the training data provided.`;
                }
                
                modelResponse = finetunedResponse;
            }
            
            if (mode === 'rag' || mode === 'both') {
                // Generate RAG response
                const ragResponse = `RAG system response for: "${query}"\n\nBased on the documents in the knowledge base, I found the following information that might help answer your question...`;
                
                if (mode === 'both') {
                    modelResponse += '\n\n---\n\n' + ragResponse;
                } else {
                    modelResponse = ragResponse;
                }
            }
            
            addMessageToChat('model', modelResponse);
        }, 1000);
        
    } catch (error) {
        console.error('Error sending chat message:', error);
        addMessageToChat('system', 'Error: Failed to get response from model. Please try again.');
    }
}

// Add message to chat
function addMessageToChat(type, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    
    messageElement.className = `${type}-message`;
    messageElement.textContent = message;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Compare answers
async function compareAnswers() {
    const query = document.getElementById('compare-query').value.trim();
    const modelId = document.getElementById('compare-model-select').value;
    
    if (!query) return;
    if (!modelId) {
        alert('Please select a model first');
        return;
    }
    
    try {
        // Show loading state
        document.getElementById('finetune-answer').innerHTML = '<p>Loading fine-tuned model response...</p>';
        document.getElementById('rag-answer').innerHTML = '<p>Loading RAG response...</p>';
        
        // In a real application, you would make API requests here
        // For example:
        /*
        const [finetuneResponse, ragResponse] = await Promise.all([
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    modelId: modelId,
                    mode: 'model'
                })
            }).then(res => res.json()),
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    modelId: modelId,
                    mode: 'rag'
                })
            }).then(res => res.json())
        ]);
        
        document.getElementById('finetune-answer').textContent = finetuneResponse.response;
        document.getElementById('rag-answer').textContent = ragResponse.response;
        */
        
        // Simulate API responses for demo purposes
        setTimeout(() => {
            // Generate fine-tuned model response
            const selectedModel = state.completedModels.find(model => model.id === modelId);
            const modelType = selectedModel.name.split('(')[1].replace(')', '').trim();
            
            let finetunedResponse;
            switch(modelType) {
                case 'qa':
                    finetunedResponse = `This is a simulated response from the fine-tuned QA model for: "${query}"`;
                    break;
                case 'reasoning':
                    finetunedResponse = `Let me think about "${query}"... \n\nAfter analyzing the question, I can provide this detailed reasoning: The answer depends on several factors including context, domain knowledge, and specific constraints.`;
                    break;
                case 'summarization':
                    finetunedResponse = `Summary of your query: "${query}" - This appears to be a question about ${query.split(' ').slice(0, 3).join(' ')}... with potential implications for further discussion.`;
                    break;
                default:
                    finetunedResponse = `Fine-tuned model response to: "${query}" - I've been specifically trained to handle this type of query based on the training data provided.`;
            }
            
            // Generate RAG response
            const ragResponse = `RAG system response for: "${query}"\n\nBased on the documents in the knowledge base, I found the following information that might help answer your question...`;
            
            document.getElementById('finetune-answer').textContent = finetunedResponse;
            document.getElementById('rag-answer').textContent = ragResponse;
        }, 1000);
        
    } catch (error) {
        console.error('Error comparing answers:', error);
        document.getElementById('finetune-answer').innerHTML = '<p class="error">Error: Failed to get response from fine-tuned model.</p>';
        document.getElementById('rag-answer').innerHTML = '<p class="error">Error: Failed to get response from RAG system.</p>';
    }
}

// Cancel a fine-tuning job
function cancelFinetuningJob(jobId) {
    const jobIndex = state.jobs.findIndex(job => job.id === jobId);
    
    if (jobIndex === -1) {
        alert('Job not found');
        return;
    }
    
    // Only allow cancellation of pending or processing jobs
    if (state.jobs[jobIndex].status !== 'PENDING' && state.jobs[jobIndex].status !== 'PROCESSING') {
        alert('Only pending or processing jobs can be cancelled');
        return;
    }
    
    // In a real application, you would make an API request here
    // For example:
    /*
    fetch(`/api/finetune/${jobId}/cancel`, {
        method: 'POST'
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to cancel job');
        }
        return response.json();
    }).then(data => {
        // Update job status in local state
        state.jobs[jobIndex].status = 'CANCELLED';
        state.jobs[jobIndex].message = 'Job cancelled by user';
        state.jobs[jobIndex].updated_at = new Date().toISOString();
        saveJobsToLocalStorage();
        updateJobStatusUI();
    }).catch(error => {
        console.error('Error cancelling job:', error);
        alert('Failed to cancel job: ' + error.message);
    });
    */
    
    // For demo purposes, we'll just update the local state
    state.jobs[jobIndex].status = 'CANCELLED';
    state.jobs[jobIndex].message = 'Job cancelled by user';
    state.jobs[jobIndex].updated_at = new Date().toISOString();
    saveJobsToLocalStorage();
    updateJobStatusUI();
}

// Delete a fine-tuning job
function deleteFinetuningJob(jobId) {
    const jobIndex = state.jobs.findIndex(job => job.id === jobId);
    
    if (jobIndex === -1) {
        alert('Job not found');
        return;
    }
    
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
        return;
    }
    
    // In a real application, you would make an API request here
    // For example:
    /*
    fetch(`/api/finetune/${jobId}`, {
        method: 'DELETE'
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete job');
        }
        
        // Remove job from local state
        state.jobs.splice(jobIndex, 1);
        
        // If the job had a completed model, remove it from completedModels
        const modelIndex = state.completedModels.findIndex(model => model.id === jobId);
        if (modelIndex !== -1) {
            state.completedModels.splice(modelIndex, 1);
        }
        
        saveJobsToLocalStorage();
        updateJobStatusUI();
        updateModelSelectOptions();
    }).catch(error => {
        console.error('Error deleting job:', error);
        alert('Failed to delete job: ' + error.message);
    });
    */
    
    // For demo purposes, we'll just update the local state
    state.jobs.splice(jobIndex, 1);
    
    // If the job had a completed model, remove it from completedModels
    const modelIndex = state.completedModels.findIndex(model => model.id === jobId);
    if (modelIndex !== -1) {
        state.completedModels.splice(modelIndex, 1);
    }
    
    saveJobsToLocalStorage();
    updateJobStatusUI();
    updateModelSelectOptions();
}

// View job details
function viewJobDetails(jobId) {
    const job = state.jobs.find(job => job.id === jobId);
    
    if (!job) {
        alert('Job not found');
        return;
    }
    
    // Create modal for job details
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Job Details</h2>
            <div class="job-details-container">
                <div class="detail-row">
                    <div class="detail-label">Job ID:</div>
                    <div class="detail-value">${job.id}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Model:</div>
                    <div class="detail-value">${job.model}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Type:</div>
                    <div class="detail-value">${job.type}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Status:</div>
                    <div class="detail-value">
                        <span class="status-badge status-${job.status.toLowerCase()}">${job.status}</span>
                    </div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Message:</div>
                    <div class="detail-value">${job.message}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Created:</div>
                    <div class="detail-value">${formatDate(job.created_at)}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Updated:</div>
                    <div class="detail-value">${formatDate(job.updated_at)}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Source Job IDs:</div>
                    <div class="detail-value">${job.jobIds.join(', ')}</div>
                </div>
                ${job.model_path ? `
                <div class="detail-row">
                    <div class="detail-label">Model Path:</div>
                    <div class="detail-value">${job.model_path}</div>
                </div>
                ` : ''}
            </div>
            <div class="modal-actions">
                ${job.status === 'COMPLETED' ? 
                    `<button class="btn btn-primary" onclick="openChatForModel('${job.id}')">Chat with Model</button>` : 
                    ''}
                ${job.status === 'PENDING' || job.status === 'PROCESSING' ? 
                    `<button class="btn btn-warning" onclick="cancelFinetuningJob('${job.id}')">Cancel Job</button>` : 
                    ''}
                <button class="btn btn-danger" onclick="deleteFinetuningJob('${job.id}')">Delete Job</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking the close button
    const closeButton = modal.querySelector('.close');
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close modal when clicking outside the modal content
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// Format file size for display
function formatFileSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' B';
    } else if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + ' KB';
    } else {
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
}

// Export chat history
function exportChatHistory() {
    const chatMessages = document.getElementById('chat-messages');
    const messages = chatMessages.querySelectorAll('div');
    
    let exportText = '';
    messages.forEach(message => {
        if (message.classList.contains('user-message')) {
            exportText += 'User: ' + message.textContent + '\n\n';
        } else if (message.classList.contains('model-message')) {
            exportText += 'Model: ' + message.textContent + '\n\n';
        } else if (message.classList.contains('system-message')) {
            exportText += 'System: ' + message.textContent + '\n\n';
        }
    });
    
    // Create a blob and download link
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat-history-' + new Date().toISOString().slice(0, 10) + '.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Clear chat history
function clearChatHistory() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '<p class="system-message">Chat history cleared. Ask a question to begin.</p>';
    }
}

// Add event listeners for additional buttons
document.addEventListener('DOMContentLoaded', () => {
    // Export chat button
    const exportChatButton = document.getElementById('export-chat');
    if (exportChatButton) {
        exportChatButton.addEventListener('click', exportChatHistory);
    }
    
    // Clear chat button
    const clearChatButton = document.getElementById('clear-chat');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', clearChatHistory);
    }
    
    // Add job details view to each job item
    function addJobDetailsListeners() {
        const jobItems = document.querySelectorAll('.job-item');
        jobItems.forEach(item => {
            item.addEventListener('click', (event) => {
                // Don't trigger if clicking on a button
                if (event.target.tagName === 'BUTTON') {
                    return;
                }
                
                const jobId = item.querySelector('.job-id').textContent.replace('Job #', '');
                viewJobDetails(jobId);
            });
        });
    }
    
    // Call once on load and then after each UI update
    const originalUpdateJobStatusUI = updateJobStatusUI;
    updateJobStatusUI = function() {
        originalUpdateJobStatusUI();
        addJobDetailsListeners();
    };
    
    // Initial call to add listeners
    addJobDetailsListeners();
    
    // Initialize tooltips if any
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseover', (e) => {
            const tooltipText = e.target.getAttribute('data-tooltip');
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'tooltip';
            tooltipEl.textContent = tooltipText;
            document.body.appendChild(tooltipEl);
            
            const rect = e.target.getBoundingClientRect();
            tooltipEl.style.top = (rect.top - tooltipEl.offsetHeight - 5) + 'px';
            tooltipEl.style.left = (rect.left + (rect.width / 2) - (tooltipEl.offsetWidth / 2)) + 'px';
        });
        
        tooltip.addEventListener('mouseout', () => {
            const tooltipEl = document.querySelector('.tooltip');
            if (tooltipEl) {
                document.body.removeChild(tooltipEl);
            }
        });
    });
});

// Function to download model weights (for demo purposes)
function downloadModelWeights(modelId) {
    const model = state.completedModels.find(m => m.id === modelId);
    if (!model) {
        alert('Model not found');
        return;
    }
    
    // In a real application, you would make an API request to download the model weights
    // For demo purposes, we'll just show an alert
    alert(`Downloading model weights for ${model.name}. This would typically start a download of the model weights file.`);
}

// Function to share a model with other users (for demo purposes)
function shareModel(modelId) {
    const model = state.completedModels.find(m => m.id === modelId);
    if (!model) {
        alert('Model not found');
        return;
    }
    
    // Create a modal for sharing
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Share Model</h2>
            <p>Share ${model.name} with other users:</p>
            <div class="share-options">
                <div class="form-group">
                    <label for="share-email">Email addresses (comma separated):</label>
                    <input type="text" id="share-email" class="form-control">
                </div>
                <div class="form-group">
                    <label for="share-permission">Permission level:</label>
                    <select id="share-permission" class="form-control">
                        <option value="view">View only</option>
                        <option value="use">Use model</option>
                        <option value="edit">Edit and use model</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="confirmShare('${modelId}')">Share</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking the close button
    const closeButton = modal.querySelector('.close');
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close modal when clicking outside the modal content
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// Confirm sharing a model (for demo purposes)
function confirmShare(modelId) {
    const emails = document.getElementById('share-email').value;
    const permission = document.getElementById('share-permission').value;
    
    if (!emails) {
        alert('Please enter at least one email address');
        return;
    }
    
    // In a real application, you would make an API request to share the model
    // For demo purposes, we'll just show an alert and close the modal
    alert(`Model shared with ${emails} with ${permission} permissions.`);
    
    // Close the modal
    const modal = document.querySelector('.modal');
    if (modal) {
        document.body.removeChild(modal);
    }
}
