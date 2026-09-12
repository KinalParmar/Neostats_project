from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health_router, documents_router

app = FastAPI(
    title="Document Intelligence Platform",
    description="API for extracting and validating financial documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])

@app.get("/")
async def root():
    return {"message": "Document Intelligence Platform API", "version": "1.0.0"}
