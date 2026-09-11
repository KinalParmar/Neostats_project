# Ollama Setup Guide (FREE Local LLM)

This platform uses Ollama to provide free, unlimited LLM queries for document extraction.

## Installation

1. **Download Ollama**: Visit https://ollama.ai and download for Windows
2. **Install**: Run the installer
3. **Pull the model**: Open a terminal and run:
   ```
   ollama pull llama3.2
   ```
4. **Verify**: Run `ollama list` to see installed models

## Configuration

The `.env` file is already configured to use Ollama:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Starting Ollama

Ollama typically starts automatically after installation. If not:
- Windows: Run Ollama from the Start menu
- It will run in the background on port 11434

## Testing

Test Ollama is working:
```bash
curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"Hello"}'
```

## Troubleshooting

- If Ollama isn't responding, check if it's running in Task Manager
- If port 11434 is blocked, check firewall settings
- For more help: https://github.com/ollama/ollama
