from sqlalchemy.orm import Session
from app.db.models import Document
from app.models.schemas import DocumentProcessingResult, FileValidationResult
from typing import List, Optional
import json


class DocumentRepository:
    """Repository for document persistence operations"""
    
    @staticmethod
    def save_document(db: Session, result: DocumentProcessingResult) -> Document:
        """Save or update a document processing result"""
        # Check if document already exists
        existing = db.query(Document).filter(
            Document.document_name == result.document_name
        ).first()
        
        document_data = {
            "document_name": result.document_name,
            "document_type": result.document_type,
            "file_validation": result.file_validation.model_dump_json(),
            "extracted_data": result.extracted_data.model_dump_json() if result.extracted_data else None,
            "financial_validations": json.dumps([v.model_dump() for v in result.financial_validations]),
            "processing_status": result.processing_status.value,
            "processing_metadata": json.dumps(result.processing_metadata),
            "error_message": result.error_message
        }
        
        if existing:
            # Update existing
            for key, value in document_data.items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new
            db_document = Document(**document_data)
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            return db_document
    
    @staticmethod
    def get_document_by_name(db: Session, document_name: str) -> Optional[Document]:
        """Get a document by name"""
        return db.query(Document).filter(
            Document.document_name == document_name
        ).first()
    
    @staticmethod
    def list_documents(db: Session) -> List[Document]:
        """Get all documents, ordered by processed time descending"""
        return db.query(Document).order_by(
            Document.processed_time.desc()
        ).all()
    
    @staticmethod
    def delete_document(db: Session, document_name: str) -> bool:
        """Delete a document by name"""
        document = db.query(Document).filter(
            Document.document_name == document_name
        ).first()
        if document:
            db.delete(document)
            db.commit()
            return True
        return False
