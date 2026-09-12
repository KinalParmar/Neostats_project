// API Configuration - Update this to your deployed backend URL
const API_BASE_URL = 'http://localhost:8002/api/v1';

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
        const response = await fetch(`${API_BASE_URL}/documents/process`, {
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
        const response = await fetch(`${API_BASE_URL}/documents/`);
        
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
                <td>${formatDate(doc.processed_at)}</td>
                <td>
                    <button class="btn-view" data-document-name="${escapeHtml(doc.document_name)}">View</button>
                </td>
            </tr>
        `).join('');
        
        // Attach event listeners to view buttons
        const viewButtons = document.querySelectorAll('.btn-view');
        console.log(`Found ${viewButtons.length} view buttons`);
        viewButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const documentName = e.target.dataset.documentName;
                console.log("View button clicked for:", documentName);
                viewDocument(documentName);
            });
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Error loading documents: ${error.message}</td></tr>`;
    }
}

// View Document Details
async function viewDocument(documentName) {
    console.log("viewDocument called with:", documentName);
    
    try {
        // Switch to detail tab
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        const detailTab = document.querySelector('[data-tab="detail"]');
        if (detailTab) {
            detailTab.classList.add('active');
            detailTab.style.display = 'inline-block';
        } else {
            console.error("Detail tab button not found");
        }
        
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        const detailContent = document.getElementById('detail');
        if (detailContent) {
            detailContent.classList.add('active');
        } else {
            console.error("Detail content div not found");
        }
        
        document.getElementById('detail-title').textContent = `Document: ${documentName}`;
        
        // Show loading state by clearing content but keeping structure
        document.getElementById('document-info').innerHTML = '<p class="loading">Loading...</p>';
        document.getElementById('file-validation').innerHTML = '';
        document.getElementById('extracted-fields').innerHTML = '';
        document.getElementById('extracted-tables').innerHTML = '';
        document.getElementById('financial-validations').innerHTML = '';
        document.getElementById('raw-json').textContent = '';
        
        console.log("Fetching document details from:", `${API_BASE_URL}/documents/${encodeURIComponent(documentName)}`);
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentName)}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load document details: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("Document data received:", data);
        renderDocumentDetails(data);
    } catch (error) {
        console.error("Error in viewDocument:", error);
        document.getElementById('document-info').innerHTML = `<p class="loading">Error: ${error.message}</p>`;
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
            <div class="info-label">Validation Status</div>
            <div class="info-value"><span class="status-badge ${data.validation?.overall_status || 'UNKNOWN'}">${data.validation?.overall_status || 'UNKNOWN'}</span></div>
        </div>
        <div class="info-item">
            <div class="info-label">Processed Time</div>
            <div class="info-value">${formatDate(data.processing_metadata?.processed_at)}</div>
        </div>
    `;
    
    // File Validation
    const validation = data.file_validation;
    document.getElementById('file-validation').innerHTML = `
        <div class="field-item ${validation.is_supported ? '' : 'missing'}">
            <div class="field-name">Supported</div>
            <div class="field-value">${validation.is_supported ? 'Yes' : 'No'}</div>
        </div>
        <div class="field-item ${validation.is_readable ? '' : 'missing'}">
            <div class="field-name">Readable</div>
            <div class="field-value">${validation.is_readable ? 'Yes' : 'No'}</div>
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
            <div class="field-name">Status</div>
            <div class="field-value"><span class="status-badge ${validation.status}">${validation.status}</span></div>
        </div>
        ${validation.errors && validation.errors.length > 0 ? `
            <div class="field-item missing">
                <div class="field-name">Errors</div>
                <div class="field-value">${validation.errors.map(e => escapeHtml(e)).join(', ')}</div>
            </div>
        ` : ''}
    `;
    
    // Extracted Fields
    const extracted = data.extracted_data;
    const fields = [];
    
    // Helper to render field with confidence
    const renderField = (name, field) => {
        if (!field || !field.value) return '';
        const confidence = field.confidence ? ` (${Math.round(field.confidence * 100)}% confidence)` : '';
        return `
            <div class="field-item">
                <div class="field-name">${escapeHtml(name)}</div>
                <div class="field-value">${escapeHtml(String(field.value))}${confidence}</div>
                <div class="field-evidence">Page ${field.page_number}</div>
            </div>
        `;
    };
    
    // Invoice fields
    if (extracted.invoice_number) fields.push(renderField('Invoice Number', extracted.invoice_number));
    if (extracted.invoice_date) fields.push(renderField('Invoice Date', extracted.invoice_date));
    if (extracted.vendor_name) fields.push(renderField('Vendor Name', extracted.vendor_name));
    if (extracted.currency) fields.push(renderField('Currency', extracted.currency));
    if (extracted.subtotal) fields.push(renderField('Subtotal', extracted.subtotal));
    if (extracted.tax_amount) fields.push(renderField('Tax Amount', extracted.tax_amount));
    if (extracted.discount) fields.push(renderField('Discount', extracted.discount));
    if (extracted.total_amount) fields.push(renderField('Total Amount', extracted.total_amount));
    
    // Balance sheet fields
    if (extracted.total_assets) fields.push(renderField('Total Assets', extracted.total_assets));
    if (extracted.total_liabilities) fields.push(renderField('Total Liabilities', extracted.total_liabilities));
    if (extracted.total_equity) fields.push(renderField('Total Equity', extracted.total_equity));
    
    // Profit & Loss fields
    if (extracted.revenue) fields.push(renderField('Revenue', extracted.revenue));
    if (extracted.expenses) fields.push(renderField('Expenses', extracted.expenses));
    if (extracted.net_profit) fields.push(renderField('Net Profit', extracted.net_profit));
    
    // Cash flow fields
    if (extracted.operating_cash_flow) fields.push(renderField('Operating Cash Flow', extracted.operating_cash_flow));
    if (extracted.investing_cash_flow) fields.push(renderField('Investing Cash Flow', extracted.investing_cash_flow));
    if (extracted.financing_cash_flow) fields.push(renderField('Financing Cash Flow', extracted.financing_cash_flow));
    if (extracted.net_cash_flow) fields.push(renderField('Net Cash Flow', extracted.net_cash_flow));
    
    if (fields.length > 0) {
        document.getElementById('extracted-fields').innerHTML = `<div class="field-grid">${fields.join('')}</div>`;
    } else {
        document.getElementById('extracted-fields').innerHTML = '<p>No fields extracted</p>';
    }
    
    // Line Items (for invoices)
    if (extracted.line_items && extracted.line_items.length > 0) {
        const tableHtml = `
            <div class="table-container">
                <h4>Line Items</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Quantity</th>
                            <th>Unit Price</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${extracted.line_items.map(item => `
                            <tr>
                                <td>${escapeHtml(item.description)}</td>
                                <td>${item.quantity}</td>
                                <td>${item.unit_price}</td>
                                <td>${item.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        document.getElementById('extracted-tables').innerHTML = tableHtml;
    } else {
        document.getElementById('extracted-tables').innerHTML = '<p>No tables extracted</p>';
    }
    
    // Financial Validations
    if (data.validation && data.validation.checks && data.validation.checks.length > 0) {
        const validationsHtml = data.validation.checks.map(v => `
            <div class="validation-item ${v.status}">
                <div class="check-name">${escapeHtml(v.name)} <span class="status ${v.status}">${v.status}</span></div>
                <div class="formula">${escapeHtml(v.formula)}</div>
                <div class="validation-details">
                    ${Object.entries(v.operands).map(([k, val]) => `<div>${escapeHtml(k)}: ${escapeHtml(String(val))}</div>`).join('')}
                    ${v.calculated_value !== null ? `<div>Calculated: ${escapeHtml(String(v.calculated_value))}</div>` : ''}
                    ${v.reported_value !== null ? `<div>Reported: ${escapeHtml(String(v.reported_value))}</div>` : ''}
                    ${v.variance !== null ? `<div>Variance: ${escapeHtml(String(v.variance))}</div>` : ''}
                </div>
            </div>
        `).join('');
        document.getElementById('financial-validations').innerHTML = validationsHtml;
    } else {
        document.getElementById('financial-validations').innerHTML = '<p>No financial validations performed</p>';
    }
    
    // Raw JSON
    document.getElementById('raw-json').textContent = JSON.stringify(data, null, 2);
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
