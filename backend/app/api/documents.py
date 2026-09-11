from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.validation.file_validator import FileValidator
from app.ocr.text_extractor import TextExtractor
from app.extraction.llm_extractor import LLMExtractor
from app.financial_validation.validator import FinancialValidator
from app.db.database import get_db
from app.db.repository import DocumentRepository
from app.models.schemas import (
    DocumentProcessingResult, 
    FileValidationResult, 
    ExtractedData, 
    ProcessingStatus,
    DocumentListItem,
    ErrorResponse
)

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
    
    # Step 1: File validation
    logger.info("Step 1: Validating file...")
    is_valid, validation_result = await FileValidator.validate_file(file)
    file_validation = FileValidationResult(**validation_result)
    
    if not is_valid:
        logger.error(f"File validation failed: {validation_result['errors']}")
        result = DocumentProcessingResult(
            document_name=file.filename or "unknown",
            document_type=document_type,
            file_validation=file_validation,
            processing_status=ProcessingStatus.FAILED,
            error_message="File validation failed: " + "; ".join(validation_result['errors']),
            processing_metadata={"stage": "file_validation"}
        )
        DocumentRepository.save_document(db, result)
        return result
    
    # Step 2: OCR/Text extraction
    logger.info("Step 2: Extracting text...")
    text_extractor = TextExtractor()
    text_by_page = []
    extraction_method = None
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract based on file type
        if file_validation.file_type == "application/pdf":
            text_by_page, extraction_method = text_extractor.extract_from_pdf(content)
        elif file_validation.file_type in ["image/jpeg", "image/jpg", "image/png"]:
            text_by_page = text_extractor.extract_from_image(content)
            extraction_method = text_by_page[0].get("extraction_method") if text_by_page else "unknown"
        
        logger.info(f"Extracted {len(text_by_page)} pages using {extraction_method}")
        
        if not text_by_page or all(not page.get("text") for page in text_by_page):
            raise Exception("No text could be extracted from the document")
            
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        result = DocumentProcessingResult(
            document_name=file.filename or "unknown",
            document_type=document_type,
            file_validation=file_validation,
            processing_status=ProcessingStatus.FAILED,
            error_message=f"Text extraction failed: {str(e)}",
            processing_metadata={"stage": "text_extraction"}
        )
        DocumentRepository.save_document(db, result)
        return result
    
    # Step 3: LLM-based field extraction
    logger.info("Step 3: Extracting structured data with LLM...")
    extracted_data = None
    try:
        llm_extractor = LLMExtractor()
        extracted = llm_extractor.extract(text_by_page, document_type)
        
        # Convert to Pydantic model
        extracted_data = ExtractedData(**extracted)
        logger.info("LLM extraction completed successfully")
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {str(e)}")
        # Continue with partial success - we have the text at least
        result = DocumentProcessingResult(
            document_name=file.filename or "unknown",
            document_type=document_type,
            file_validation=file_validation,
            extracted_data=None,
            financial_validations=[],
            processing_status=ProcessingStatus.PARTIAL,
            error_message=f"LLM extraction failed: {str(e)}",
            processing_metadata={
                "stage": "llm_extraction",
                "extraction_method": extraction_method,
                "pages_extracted": len(text_by_page)
            }
        )
        DocumentRepository.save_document(db, result)
        return result
    
    # Step 4: Financial validation
    logger.info("Step 4: Running financial validations...")
    financial_validations = []
    try:
        financial_validator = FinancialValidator()
        extracted_dict = extracted_data.model_dump()
        financial_validations = financial_validator.validate(extracted_dict, document_type)
        logger.info(f"Completed {len(financial_validations)} financial validations")
        
    except Exception as e:
        logger.error(f"Financial validation failed: {str(e)}")
        # Non-critical error, continue
    
    # Step 5: Determine overall status
    processing_status = ProcessingStatus.SUCCESS
    if any(v.get("status") == "FAIL" for v in financial_validations):
        processing_status = ProcessingStatus.PARTIAL
    
    # Step 6: Save to database
    logger.info("Step 5: Saving to database...")
    result = DocumentProcessingResult(
        document_name=file.filename or "unknown",
        document_type=document_type,
        file_validation=file_validation,
        extracted_data=extracted_data,
        financial_validations=financial_validations,
        processing_status=processing_status,
        processing_metadata={
            "extraction_method": extraction_method,
            "pages_extracted": len(text_by_page),
            "total_validations": len(financial_validations),
            "failed_validations": sum(1 for v in financial_validations if v.get("status") == "FAIL")
        }
    )
    
    DocumentRepository.save_document(db, result)
    logger.info(f"Document processing completed: {processing_status}")
    
    return result


@router.get("/{document_name}", response_model=DocumentProcessingResult)
async def get_document(document_name: str, db: Session = Depends(get_db)):
    """
    Get the latest processed result for a specific document by name
    """
    logger.info(f"Retrieving document: {document_name}")
    
    document = DocumentRepository.get_document_by_name(db, document_name)
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_name}' not found"
        )
    
    return DocumentProcessingResult(**document.to_dict())


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(db: Session = Depends(get_db)):
    """
    List all processed documents
    """
    logger.info("Listing all documents")
    
    documents = DocumentRepository.list_documents(db)
    
    return [
        DocumentListItem(
            document_name=doc.document_name,
            document_type=doc.document_type,
            processing_status=doc.processing_status,
            processed_time=doc.processed_time
        )
        for doc in documents
    ]
