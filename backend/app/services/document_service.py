from typing import Dict, Any
import time
from datetime import datetime
from fastapi import UploadFile
import logging

from app.services.document_validation_service import DocumentValidationService
from app.services.ocr_service import OCRService
from app.services.extraction_service import ExtractionService
from app.services.financial_validation_service import FinancialValidationService
from app.schemas.document import DocumentProcessingResult, FileValidation

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for orchestrating document processing pipeline"""
    
    def __init__(self, use_ollama: bool = True, ollama_base_url: str = "http://localhost:11434", ollama_model: str = "llama3.2"):
        self.validation_service = DocumentValidationService()
        self.ocr_service = OCRService()
        self.extraction_service = ExtractionService(use_ollama, ollama_base_url, ollama_model)
        self.financial_validation_service = FinancialValidationService()
    
    async def process_document(
        self, 
        file: UploadFile, 
        document_type: str
    ) -> DocumentProcessingResult:
        """
        Process document through the complete pipeline:
        1. File validation
        2. OCR/Text extraction
        3. Structured data extraction
        4. Financial validation
        """
        start_time = time.time()
        
        # Step 1: File validation
        logger.info(f"Validating file: {file.filename}")
        file_validation = await self.validation_service.validate_file(file)
        
        if file_validation.status != "PASS":
            return DocumentProcessingResult(
                document_name=file.filename,
                document_type=document_type,
                file_validation=file_validation,
                extracted_data={},
                validation={"checks": [], "overall_status": "FAIL", "issues": file_validation.errors},
                processing_metadata={
                    "ocr_used": False,
                    "processed_at": datetime.utcnow(),
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                },
                error="File validation failed"
            )
        
        # Read file content
        content = await file.read()
        
        # Step 2: OCR/Text extraction
        logger.info(f"Extracting text from: {file.filename}")
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        if file_ext == 'pdf':
            text_by_page, extraction_method = self.ocr_service.extract_from_pdf(content)
        else:
            text_by_page, extraction_method = self.ocr_service.extract_from_image(content)
        
        ocr_used = extraction_method == "ocr"
        file_validation.page_count = len(text_by_page)
        
        if not text_by_page:
            logger.warning(f"No text extracted from: {file.filename}")
            return DocumentProcessingResult(
                document_name=file.filename,
                document_type=document_type,
                file_validation=file_validation,
                extracted_data={},
                validation={"checks": [], "overall_status": "PARTIAL", "issues": ["No text extracted from document"]},
                processing_metadata={
                    "ocr_used": ocr_used,
                    "processed_at": datetime.utcnow(),
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "extraction_method": extraction_method,
                    "pages_extracted": 0
                },
                error="No text extracted"
            )
        
        # Step 3: Structured data extraction
        logger.info(f"Extracting structured data from: {file.filename}")
        extracted_data = self.extraction_service.extract(text_by_page, document_type)
        
        # Step 4: Financial validation
        logger.info(f"Validating financial data for: {file.filename}")
        validation = self.financial_validation_service.validate(extracted_data, document_type)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return DocumentProcessingResult(
            document_name=file.filename,
            document_type=document_type,
            file_validation=file_validation,
            extracted_data=extracted_data,
            validation=validation,
            processing_metadata={
                "ocr_used": ocr_used,
                "processed_at": datetime.utcnow(),
                "processing_time_ms": processing_time_ms,
                "extraction_method": extraction_method,
                "pages_extracted": len(text_by_page)
            }
        )
