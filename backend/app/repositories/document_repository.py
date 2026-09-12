from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document persistence"""
    
    def save_document(self, db: Session, document_data: dict) -> bool:
        """
        Save document processing result to database
        """
        try:
            # For now, we'll use a simple JSON file-based storage
            # In production, this would use SQLAlchemy models
            import json
            import os
            
            storage_dir = "processed_documents"
            os.makedirs(storage_dir, exist_ok=True)
            
            filename = document_data["document_name"].replace("/", "_").replace("\\", "_")
            filepath = os.path.join(storage_dir, f"{filename}.json")
            
            with open(filepath, 'w') as f:
                json.dump(document_data, f, indent=2, default=str)
            
            logger.info(f"Document saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return False
    
    def get_document_by_name(self, db: Session, document_name: str) -> Optional[dict]:
        """
        Retrieve document by name
        """
        try:
            import json
            import os
            
            storage_dir = "processed_documents"
            filename = document_name.replace("/", "_").replace("\\", "_")
            filepath = os.path.join(storage_dir, f"{filename}.json")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
            return None
    
    def list_documents(self, db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        List all processed documents
        """
        try:
            import json
            import os
            
            storage_dir = "processed_documents"
            if not os.path.exists(storage_dir):
                return []
            
            documents = []
            for filename in os.listdir(storage_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(storage_dir, filename)
                    with open(filepath, 'r') as f:
                        doc = json.load(f)
                        documents.append({
                            "document_name": doc.get("document_name"),
                            "document_type": doc.get("document_type"),
                            "processed_at": doc.get("processing_metadata", {}).get("processed_at"),
                            "processing_status": doc.get("validation", {}).get("overall_status", "UNKNOWN"),
                            "file_type": doc.get("file_validation", {}).get("file_type", "unknown")
                        })
            
            return documents[skip:skip+limit]
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
