from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class FieldExtraction(BaseModel):
    value: Any
    confidence: Optional[float] = Field(None, description="Confidence score 0-1")
    page_number: int = Field(1, description="Page number where field was found")


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class ExtractedData(BaseModel):
    invoice_number: Optional[FieldExtraction] = None
    invoice_date: Optional[FieldExtraction] = None
    vendor_name: Optional[FieldExtraction] = None
    currency: Optional[FieldExtraction] = None
    subtotal: Optional[FieldExtraction] = None
    tax_amount: Optional[FieldExtraction] = None
    discount: Optional[FieldExtraction] = None
    total_amount: Optional[FieldExtraction] = None
    line_items: List[LineItem] = Field(default_factory=list)
    
    # Balance sheet fields
    total_assets: Optional[FieldExtraction] = None
    total_liabilities: Optional[FieldExtraction] = None
    total_equity: Optional[FieldExtraction] = None
    
    # Profit & Loss fields
    revenue: Optional[FieldExtraction] = None
    expenses: Optional[FieldExtraction] = None
    net_profit: Optional[FieldExtraction] = None
    
    # Cash flow fields
    operating_cash_flow: Optional[FieldExtraction] = None
    investing_cash_flow: Optional[FieldExtraction] = None
    financing_cash_flow: Optional[FieldExtraction] = None
    net_cash_flow: Optional[FieldExtraction] = None


class ValidationCheck(BaseModel):
    name: str
    formula: str
    operands: Dict[str, float] = Field(default_factory=dict)
    calculated_value: Optional[float] = None
    reported_value: Optional[float] = None
    variance: Optional[float] = None
    status: str = Field(..., description="PASS, FAIL, or NOT_APPLICABLE")


class Validation(BaseModel):
    checks: List[ValidationCheck] = Field(default_factory=list)
    overall_status: str = Field(..., description="PASS, FAIL, or PARTIAL")
    issues: List[str] = Field(default_factory=list)


class FileValidation(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int
    status: str = Field(..., description="PASS or FAIL")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProcessingMetadata(BaseModel):
    ocr_used: bool
    processed_at: datetime
    processing_time_ms: int
    extraction_method: Optional[str] = None
    pages_extracted: Optional[int] = None


class DocumentProcessingResult(BaseModel):
    document_name: str
    document_type: str
    file_validation: FileValidation
    extracted_data: ExtractedData
    validation: Validation
    processing_metadata: ProcessingMetadata
    error: Optional[str] = None


class DocumentListItem(BaseModel):
    document_name: str
    document_type: str
    processed_at: datetime
    processing_status: str
    file_type: str


class ErrorResponse(BaseModel):
    error: Dict[str, str]
