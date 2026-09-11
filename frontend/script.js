// API Configuration - Update this to your deployed backend URL
const API_BASE_URL = 'http://localhost:8001';

// Tab Navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show corresponding tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
        
        // Load dashboard if switching to dashboard tab
        if (tabId === 'dashboard') {
            loadDocuments();
        }
    });
});

// Document Upload Form
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const documentType = document.getElementById('document-type').value;
    const file = fileInput.files[0];
    
    if (!file) {
        showResult('error', 'Please select a file');
        return;
    }
    
    if (!documentType) {
        showResult('error', 'Please select a document type');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    
    const processBtn = document.getElementById('process-btn');
    const btnText = processBtn.querySelector('.btn-text');
    const btnLoading = processBtn.querySelector('.btn-loading');
    
    // Show loading state
    processBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/documents/process`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResult('success', `Document processed successfully: ${data.document_name}`);
            fileInput.value = '';
        } else {
            showResult('error', data.error || data.detail || 'Processing failed');
        }
    } catch (error) {
        showResult('error', `Network error: ${error.message}`);
    } finally {
        processBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
});

function showResult(type, message) {
    const resultPanel = document.getElementById('upload-result');
    resultPanel.className = `result-panel ${type}`;
    resultPanel.textContent = message;
    resultPanel.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        resultPanel.style.display = 'none';
    }, 5000);
}

// Load Documents Dashboard
async function loadDocuments() {
    const tbody = document.getElementById('documents-table-body');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/documents/`);
        
        if (!response.ok) {
            throw new Error('Failed to load documents');
        }
        
        const documents = await response.json();
        
        if (documents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No documents processed yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = documents.map(doc => `
            <tr>
                <td>${escapeHtml(doc.document_name)}</td>
                <td>${formatDocumentType(doc.document_type)}</td>
                <td><span class="status-badge ${doc.processing_status}">${doc.processing_status}</span></td>
                <td>${formatDate(doc.processed_time)}</td>
                <td>
                    <button class="btn-view" onclick="viewDocument('${escapeHtml(doc.document_name)}')">View</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Error loading documents: ${error.message}</td></tr>`;
    }
}

// View Document Details
async function viewDocument(documentName) {
    // Switch to detail tab
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-tab="detail"]').classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('detail').classList.add('active');
    
    document.getElementById('detail-title').textContent = `Document: ${documentName}`;
    
    // Show loading state
    document.getElementById('detail-content').innerHTML = '<p class="loading">Loading...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(documentName)}`);
        
        if (!response.ok) {
            throw new Error('Failed to load document details');
        }
        
        const data = await response.json();
        renderDocumentDetails(data);
    } catch (error) {
        document.getElementById('detail-content').innerHTML = `<p class="loading">Error: ${error.message}</p>`;
    }
}

function renderDocumentDetails(data) {
    // Document Info
    document.getElementById('document-info').innerHTML = `
        <div class="info-item">
            <div class="info-label">Name</div>
            <div class="info-value">${escapeHtml(data.document_name)}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Type</div>
            <div class="info-value">${formatDocumentType(data.document_type)}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Status</div>
            <div class="info-value"><span class="status-badge ${data.processing_status}">${data.processing_status}</span></div>
        </div>
        <div class="info-item">
            <div class="info-label">Processed Time</div>
            <div class="info-value">${formatDate(data.processed_time)}</div>
        </div>
    `;
    
    // File Validation
    const validation = data.file_validation;
    document.getElementById('file-validation').innerHTML = `
        <div class="field-item ${validation.valid ? '' : 'missing'}">
            <div class="field-name">Valid</div>
            <div class="field-value">${validation.valid ? 'Yes' : 'No'}</div>
        </div>
        <div class="field-item">
            <div class="field-name">File Type</div>
            <div class="field-value">${escapeHtml(validation.file_type || 'N/A')}</div>
        </div>
        <div class="field-item">
            <div class="field-name">Page Count</div>
            <div class="field-value">${validation.page_count || 'N/A'}</div>
        </div>
        <div class="field-item">
            <div class="field-name">File Size</div>
            <div class="field-value">${validation.file_size ? formatBytes(validation.file_size) : 'N/A'}</div>
        </div>
        ${validation.errors.length > 0 ? `
            <div class="field-item missing">
                <div class="field-name">Errors</div>
                <div class="field-value">${validation.errors.map(e => escapeHtml(e)).join(', ')}</div>
            </div>
        ` : ''}
    `;
    
    // Extracted Fields
    if (data.extracted_data && data.extracted_data.fields) {
        const fieldsHtml = Object.entries(data.extracted_data.fields).map(([key, value]) => `
            <div class="field-item ${value.value === null ? 'missing' : ''}">
                <div class="field-name">${escapeHtml(key)}</div>
                <div class="field-value">${value.value === null ? 'Not found' : escapeHtml(String(value.value))}</div>
                ${value.evidence ? `<div class="field-evidence">Evidence: ${escapeHtml(value.evidence)} (Page ${value.page_number})</div>` : ''}
            </div>
        `).join('');
        document.getElementById('extracted-fields').innerHTML = `<div class="field-grid">${fieldsHtml}</div>`;
    } else {
        document.getElementById('extracted-fields').innerHTML = '<p>No fields extracted</p>';
    }
    
    // Tables
    if (data.extracted_data && data.extracted_data.tables && data.extracted_data.tables.length > 0) {
        const tablesHtml = data.extracted_data.tables.map((table, idx) => `
            <div class="table-container">
                <h4>${escapeHtml(table.name || `Table ${idx + 1}`)}</h4>
                <table>
                    <thead>
                        <tr>
                            ${table.headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${table.rows.map(row => `
                            <tr>
                                ${table.headers.map(h => `<td>${escapeHtml(String(row[h] || ''))}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `).join('');
        document.getElementById('extracted-tables').innerHTML = tablesHtml;
    } else {
        document.getElementById('extracted-tables').innerHTML = '<p>No tables extracted</p>';
    }
    
    // Financial Validations
    if (data.financial_validations && data.financial_validations.length > 0) {
        const validationsHtml = data.financial_validations.map(v => `
            <div class="validation-item ${v.status}">
                <div class="check-name">${escapeHtml(v.check_name)} <span class="status ${v.status}">${v.status}</span></div>
                <div class="formula">${escapeHtml(v.formula)}</div>
                <div class="validation-details">
                    ${Object.entries(v.inputs).map(([k, val]) => `<div>${escapeHtml(k)}: ${escapeHtml(val)}</div>`).join('')}
                    ${v.calculated_value !== null ? `<div>Calculated: ${escapeHtml(v.calculated_value)}</div>` : ''}
                    ${v.reported_value !== null ? `<div>Reported: ${escapeHtml(v.reported_value)}</div>` : ''}
                    ${v.variance !== null ? `<div>Variance: ${escapeHtml(v.variance)}</div>` : ''}
                </div>
            </div>
        `).join('');
        document.getElementById('financial-validations').innerHTML = validationsHtml;
    } else {
        document.getElementById('financial-validations').innerHTML = '<p>No financial validations performed</p>';
    }
    
    // Raw JSON
    document.getElementById('raw-json').textContent = JSON.stringify(data, null, 2);
    
    // Restore detail content structure
    restoreDetailStructure();
}

function restoreDetailStructure() {
    document.getElementById('detail-content').innerHTML = `
        <div class="detail-section">
            <h3>Document Information</h3>
            <div id="document-info"></div>
        </div>
        <div class="detail-section">
            <h3>File Validation</h3>
            <div id="file-validation"></div>
        </div>
        <div class="detail-section">
            <h3>Extracted Fields</h3>
            <div id="extracted-fields"></div>
        </div>
        <div class="detail-section">
            <h3>Tables</h3>
            <div id="extracted-tables"></div>
        </div>
        <div class="detail-section">
            <h3>Financial Validations</h3>
            <div id="financial-validations"></div>
        </div>
        <div class="detail-section">
            <h3>Raw JSON</h3>
            <button class="btn btn-secondary" id="toggle-json">Toggle Raw JSON</button>
            <pre id="raw-json" style="display: none;"></pre>
        </div>
    `;
    
    // Re-attach toggle event
    document.getElementById('toggle-json').addEventListener('click', () => {
        const rawJson = document.getElementById('raw-json');
        rawJson.style.display = rawJson.style.display === 'none' ? 'block' : 'none';
    });
}

// Back to Dashboard
document.getElementById('back-to-dashboard').addEventListener('click', () => {
    document.querySelector('[data-tab="dashboard"]').click();
});

// Toggle Raw JSON
document.getElementById('toggle-json').addEventListener('click', () => {
    const rawJson = document.getElementById('raw-json');
    rawJson.style.display = rawJson.style.display === 'none' ? 'block' : 'none';
});

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDocumentType(type) {
    const types = {
        'invoice': 'Invoice',
        'balance_sheet': 'Balance Sheet',
        'profit_loss': 'Profit & Loss',
        'cash_flow': 'Cash Flow'
    };
    return types[type] || type;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Load documents on page load if starting on dashboard
if (document.getElementById('dashboard').classList.contains('active')) {
    loadDocuments();
}
