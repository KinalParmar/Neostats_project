from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from app.db.database import Base
import json


class Document(Base):
    """Database model for processed documents"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, unique=True, index=True, nullable=False)
    document_type = Column(String, nullable=False)
    file_validation = Column(Text, nullable=False)  # JSON string
    extracted_data = Column(Text, nullable=True)  # JSON string
    financial_validations = Column(Text, nullable=True)  # JSON string
    processing_status = Column(String, nullable=False)
    processing_metadata = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    processed_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "file_validation": json.loads(self.file_validation) if self.file_validation else None,
            "extracted_data": json.loads(self.extracted_data) if self.extracted_data else None,
            "financial_validations": json.loads(self.financial_validations) if self.financial_validations else [],
            "processing_status": self.processing_status,
            "processing_metadata": json.loads(self.processing_metadata) if self.processing_metadata else {},
            "error_message": self.error_message,
            "processed_time": self.processed_time.isoformat() if self.processed_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None
        }
