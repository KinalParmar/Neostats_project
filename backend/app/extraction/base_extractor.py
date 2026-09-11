from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Base class for document-type-specific extractors"""
    
    @abstractmethod
    def extract(self, text_by_page: List[Dict[str, Any]], document_type: str) -> Dict[str, Any]:
        """
        Extract structured data from OCR'd text.
        Returns structured key-value pairs and tables.
        """
        pass
