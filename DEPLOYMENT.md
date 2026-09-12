# Deployment Instructions

## Frontend (Vercel) - Already Deployed
Frontend is deployed at: https://neostats-project-87bkatno5-kinalparmars-projects.vercel.app/

## Backend (Render) - Deployment Steps

### Option 1: Deploy to Render (Recommended)

1. **Create a Render account** at https://render.com

2. **Push backend code to GitHub**
   - Initialize git in the backend folder
   - Push to a GitHub repository

3. **Create a new Web Service on Render**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Select the `backend` folder as root directory
   - Configure:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables**:
       - `PORT`: `8002`
       - `OLLAMA_BASE_URL`: Your Ollama instance URL (if using external)
   
4. **Deploy** - Render will automatically build and deploy

5. **Get the backend URL** from Render (e.g., `https://your-backend.onrender.com`)

### Option 2: Deploy to Railway

1. **Create Railway account** at https://railway.app

2. **Deploy from GitHub**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will detect Python and auto-configure
   - Add environment variables as needed

### Option 3: Deploy to Koyeb

1. **Create Koyeb account** at https://www.koyeb.com

2. **Deploy using git**
   - Click "Create App" → "Git"
   - Connect your GitHub repository
   - Configure build and run commands

## Update Frontend API URL

After deploying the backend:

1. Update the API_BASE_URL in `frontend/script.js`:
   ```javascript
   const API_BASE_URL = 'https://your-backend-url.onrender.com/api/v1';
   ```

2. Push changes to GitHub
3. Vercel will auto-redeploy

## Important Notes

- **Ollama Requirement**: The backend requires Ollama for LLM extraction. For production:
  - Run Ollama on a separate server
  - Set `OLLAMA_BASE_URL` environment variable to point to your Ollama instance
  - Or use a cloud LLM service (OpenAI, Anthropic, etc.) by modifying the extraction service

- **File Storage**: Currently uses local JSON file storage. For production:
  - Use a database (PostgreSQL, MongoDB)
  - Or cloud storage (AWS S3, Google Cloud Storage)

- **OCR**: EasyOCR is used for OCR. For production:
  - Consider using cloud OCR services (AWS Textract, Google Vision API)
