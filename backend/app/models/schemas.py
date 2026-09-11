from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    INVOICE = "invoice"
    BALANCE_SHEET = "balance_sheet"
    PROFIT_LOSS = "profit_loss"
    CASH_FLOW = "cash_flow"


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class FileValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    file_type: Optional[str] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    filename: Optional[str] = None


class Evidence(BaseModel):
    value: Optional[str] = None
    evidence: Optional[str] = None
    page_number: Optional[int] = None


class TableData(BaseModel):
    name: Optional[str] = None
    headers: List[str] = []
    rows: List[Dict[str, Any]] = []
    evidence: Optional[str] = None
    page_number: Optional[int] = None


class ValidationResult(BaseModel):
    check_name: str
    formula: str
    inputs: Dict[str, str] = {}
    calculated_value: Optional[str] = None
    reported_value: Optional[str] = None
    variance: Optional[str] = None
    status: str  # PASS, FAIL, NOT_APPLICABLE


class ExtractionMetadata(BaseModel):
    model_used: Optional[str] = None
    document_type: Optional[str] = None
    total_pages: Optional[int] = None
    extraction_method: Optional[str] = None


class ExtractedData(BaseModel):
    fields: Dict[str, Evidence] = {}
    tables: List[TableData] = []
    extraction_metadata: Optional[ExtractionMetadata] = None


class DocumentProcessingResult(BaseModel):
    document_name: str
    document_type: str
    file_validation: FileValidationResult
    extracted_data: Optional[ExtractedData] = None
    financial_validations: List[ValidationResult] = []
    processing_status: ProcessingStatus
    processing_metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    processed_time: datetime = Field(default_factory=datetime.utcnow)


class DocumentListItem(BaseModel):
    document_name: str
    document_type: str
    processing_status: ProcessingStatus
    processed_time: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int
