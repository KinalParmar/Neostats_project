# Document Intelligence Platform

A comprehensive platform for extracting and validating financial documents using AI with **FREE unlimited LLM queries** via Ollama.

## Overview

This platform provides:
- Document upload and processing (PDF, JPG, PNG)
- OCR-based text extraction with EasyOCR and Tesseract fallback
- **FREE unlimited LLM-powered structured data extraction** using Ollama (local LLM)
- Financial validation (balance sheet equations, invoice totals, etc.)
- REST API with Swagger documentation
- Web dashboard for viewing results
- Rule-based fallback extraction when LLM is unavailable

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: Plain HTML/CSS/JavaScript
- **OCR**: EasyOCR (primary), Tesseract (fallback)
- **LLM**: Ollama with Llama3.2 (FREE local LLM) or OpenAI (optional)
- **Database**: SQLite
- **PDF Processing**: pdfplumber, PyMuPDF

## Local Setup

### Prerequisites

- Python 3.9 or higher
- (Recommended) Ollama for FREE local LLM
- (Optional) Tesseract OCR for enhanced OCR

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd document-intelligence-platform
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Run the setup script (Windows)
cd ..
.\setup_env.bat
```

Or manually create `backend/.env`:
```bash
DATABASE_URL=sqlite:///./document_intelligence.db
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
HOST=0.0.0.0
PORT=8000
```

4. (Recommended) Install Ollama for FREE local LLM:
   - Download from https://ollama.ai
   - Install and run: `ollama pull llama3.2`
   - See [SETUP_OLLAMA.md](SETUP_OLLAMA.md) for detailed instructions

5. Initialize database:
```bash
cd backend
python -c "from app.db.database import init_db; init_db()"
```

6. Run the backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. Open frontend in browser:
```bash
cd ../frontend
python -m http.server 3000
```

8. Access the application:
   - Frontend: http://localhost:3000
   - Swagger UI: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

## Environment Variables

See `backend/.env.example`:
- `DATABASE_URL`: SQLite database path
- `LLM_PROVIDER`: "ollama" (FREE) or "openai" (requires API key)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llama3.2)
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4-turbo-preview)

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### API Endpoints

- `POST /api/documents/process` - Upload and process a document
- `GET /api/documents/{document_name}` - Get processed document by name
- `GET /api/documents/` - List all processed documents
- `GET /api/health` - Health check

### API Request Examples

**Process a document:**
```bash
curl -X POST "http://localhost:8000/api/documents/process" \
  -F "file=@document.pdf" \
  -F "document_type=invoice"
```

**Get document by name:**
```bash
curl "http://localhost:8000/api/documents/document.pdf"
```

**List all documents:**
```bash
curl "http://localhost:8000/api/documents/"
```

## Financial Validation Rules

- **Invoices**: Subtotal + Tax = Total (tolerance: 0.01)
- **Balance Sheet**: Assets = Liabilities + Equity (tolerance: 0.01)
- **Profit & Loss**: Revenue - Expenses = Net Profit (tolerance: 0.01)
- **Cash Flow**: Opening Balance + Net Change = Closing Balance (tolerance: 0.01)

## OCR Services Used

- **Primary**: EasyOCR (deep learning-based, no external installation required)
- **Fallback**: Tesseract OCR (requires external installation)
- For native-text PDFs: Direct text extraction via pdfplumber/PyMuPDF

## LLM Services Used

- **Primary**: Ollama with Llama3.2 (FREE local LLM, unlimited queries)
- **Fallback**: Rule-based extraction using regex patterns
- **Optional**: OpenAI GPT-4 (requires API key, not free)

## Testing

Run automated tests:
```bash
cd backend
pytest
```

## Known Limitations

- Max 3 pages per document
- OCR quality depends on image quality
- Ollama requires local installation for FREE LLM
- No document auto-classification (user must select type)
- Rule-based fallback extraction is less comprehensive than LLM

## Production Considerations

For production deployment:
- Use PostgreSQL instead of SQLite
- Add authentication/authorization
- Implement rate limiting
- Add comprehensive logging and monitoring
- Use a queue system for async processing
- Add caching for frequently accessed documents
- Implement proper error recovery and retries
- Deploy Ollama on a separate server with GPU for better performance

## AI Coding Assistants Used

Built with assistance from Cascade (Windsurf AI) for:
- Repository scaffolding
- Code implementation
- Debugging and testing
- Architecture design
