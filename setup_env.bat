@echo off
echo Creating .env file with Ollama configuration...
echo.

(
echo # Database
echo DATABASE_URL=sqlite:///./document_intelligence.db
echo.
echo # LLM Configuration - Using Ollama (FREE local LLM)
echo LLM_PROVIDER=ollama
echo OLLAMA_BASE_URL=http://localhost:11434
echo OLLAMA_MODEL=llama3.2
echo.
echo # OpenAI Configuration (optional - if you want to use OpenAI instead)
echo # OPENAI_API_KEY=your_openai_api_key_here
echo # OPENAI_BASE_URL=https://api.openai.com/v1
echo # OPENAI_MODEL=gpt-4-turbo-preview
echo.
echo # OCR Configuration
echo TESSERACT_CMD=tesseract
echo # TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
echo.
echo # Server Configuration
echo HOST=0.0.0.0
echo PORT=8000
) > backend\.env

echo .env file created successfully!
echo.
echo IMPORTANT: To use Ollama (FREE local LLM):
echo 1. Download and install Ollama from https://ollama.ai
echo 2. Run: ollama pull llama3.2
echo 3. Start Ollama server (it usually starts automatically)
echo.
pause
