from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.services.document_service import DocumentService
from app.repositories.document_repository import DocumentRepository
from app.db.database import get_db
from app.schemas.document import DocumentProcessingResult, DocumentListItem, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=DocumentProcessingResult)
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Process a document (PDF, JPG, PNG) and extract structured data.
    Document type must be one of: invoice, balance_sheet, profit_loss, cash_flow
    """
    logger.info(f"Processing document: {file.filename}, type: {document_type}")
    
    # Validate document type
    valid_types = ["invoice", "balance_sheet", "profit_loss", "cash_flow"]
    if document_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Initialize document service
    document_service = DocumentService()
    
    # Process document
    try:
        result = await document_service.process_document(file, document_type)
        
        # Save to repository
        repository = DocumentRepository()
        repository.save_document(db, result.dict())
        
        return result
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_name}", response_model=DocumentProcessingResult)
async def get_document(
    document_name: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a processed document by name
    """
    logger.info(f"Retrieving document: {document_name}")
    
    repository = DocumentRepository()
    document = repository.get_document_by_name(db, document_name)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentProcessingResult(**document)


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all processed documents
    """
    logger.info(f"Listing documents: skip={skip}, limit={limit}")
    
    repository = DocumentRepository()
    documents = repository.list_documents(db, skip=skip, limit=limit)
    
    return [DocumentListItem(**doc) for doc in documents]
