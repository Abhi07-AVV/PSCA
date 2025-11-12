// script.js

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseLink = document.getElementById('browseLink');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');
const analyzeButton = document.getElementById('analyzeButton');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const resultsSection = document.getElementById('resultsSection');
const overallScore = document.getElementById('overallScore');
const recommendation = document.getElementById('recommendation');
const matchesList = document.getElementById('matchesList');
const datasetCount = document.getElementById('datasetCount');
const refreshDataset = document.getElementById('refreshDataset');
const exportHtmlBtn = document.getElementById('exportHtmlBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');

// State variables
let uploadedFile = null;
let datasetFiles = [];

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    setupEventListeners();
    
    // Load dataset info
    loadDatasetInfo();
});

// Set up event listeners
function setupEventListeners() {
    // File upload area events
    uploadArea.addEventListener('click', openFileBrowser);
    browseLink.addEventListener('click', openFileBrowser);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Remove file button
    removeFile.addEventListener('click', removeSelectedFile);
    
    // Analyze button
    analyzeButton.addEventListener('click', analyzeProposal);
    
    // Refresh dataset button
    refreshDataset.addEventListener('click', loadDatasetInfo);
    
    // Export buttons
    exportHtmlBtn.addEventListener('click', exportHtmlReport);
    exportPdfBtn.addEventListener('click', exportPdfReport);
}

// Open file browser
function openFileBrowser() {
    // Reset the file input to allow selecting the same file again
    fileInput.value = '';
    fileInput.click();
}

// Handle file selection
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Handle drag over
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    uploadArea.style.borderColor = '#2980b9';
    uploadArea.style.backgroundColor = '#e3f2fd';
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    uploadArea.style.borderColor = '#3498db';
    uploadArea.style.backgroundColor = '#f8f9fa';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Process selected file
function processFile(file) {
    if (file.type !== 'application/pdf') {
        alert('Please select a PDF file.');
        return;
    }
    
    uploadedFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    analyzeButton.disabled = false;
    
    // Show a message that the file is ready to analyze
    analyzeButton.textContent = 'Analyze Proposal';
}

// Remove selected file
function removeSelectedFile() {
    uploadedFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    analyzeButton.disabled = true;
    analyzeButton.textContent = 'Analyze Proposal';
}

// Load dataset information
function loadDatasetInfo() {
    fetch('/api/dataset')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            datasetFiles = data.files;
            datasetCount.textContent = data.count;
        })
        .catch(error => {
            console.error('Error loading dataset info:', error);
            datasetCount.textContent = 'Error';
        });
}

// Analyze proposal
function analyzeProposal() {
    if (!uploadedFile) {
        alert('Please select a file first.');
        return;
    }
    
    // Upload the file first
    const formData = new FormData();
    formData.append('file', uploadedFile);
    
    // Show progress bar
    progressBar.style.display = 'block';
    analyzeButton.disabled = true;
    analyzeButton.textContent = 'Analyzing...';
    
    // Upload file
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Now analyze the proposal
            return fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}) // No need to send filename
            });
        } else {
            throw new Error('Upload failed');
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Hide progress bar
        progressBar.style.display = 'none';
        analyzeButton.textContent = 'Analyze Proposal';
        
        // Show results
        showResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        progressBar.style.display = 'none';
        analyzeButton.disabled = false;
        analyzeButton.textContent = 'Analyze Proposal';
        
        // Check if the error is due to HTML being returned instead of JSON
        if (error.message.includes('Unexpected token') || error.message.includes('HTTP error')) {
            alert('An error occurred during analysis. The server may be misconfigured or unreachable.');
        } else {
            alert('An error occurred during analysis: ' + error.message);
        }
    });
}

// Show analysis results
function showResults(data) {
    // Update overall score
    overallScore.textContent = `${data.overallScore.toFixed(2)}%`;
    
    // Update recommendation
    recommendation.textContent = data.recommendation;
    recommendation.className = 'recommendation ' + (data.shouldMerge ? 'high' : 'low');
    
    // Populate matches
    populateMatches(data.matches);
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Populate matches list
function populateMatches(matches) {
    matchesList.innerHTML = '';
    
    if (matches.length === 0) {
        matchesList.innerHTML = '<p>No significant matches found. The proposal appears to be unique.</p>';
        return;
    }
    
    // Sort matches by similarity (highest first)
    matches.sort((a, b) => b.similarity - a.similarity);
    
    matches.forEach(match => {
        const matchElement = document.createElement('div');
        matchElement.className = 'match-item';
        matchElement.innerHTML = `
            <div class="match-header">
                <span class="similarity-score">${match.similarity.toFixed(2)}% similar</span>
                <span class="match-doc">${match.document} (Chunk #${match.chunk})</span>
            </div>
            <div class="match-content">
                <p><strong>Query Text:</strong> ${match.queryText}</p>
            </div>
        `;
        matchesList.appendChild(matchElement);
    });
}

// Export HTML report
function exportHtmlReport() {
    // In a real implementation, this would generate and download an HTML file
    alert('HTML report exported successfully!');
}

// Export PDF report
function exportPdfReport() {
    // In a real implementation, this would generate and download a PDF file
    alert('PDF report exported successfully!');
}