from fastapi import UploadFile
from typing import Tuple, Dict, Any
import logging
from app.schemas.document import FileValidation

logger = logging.getLogger(__name__)


class DocumentValidationService:
    """Service for validating uploaded documents"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_PAGES = 3
    
    @staticmethod
    async def validate_file(file: UploadFile) -> FileValidation:
        """
        Validate uploaded file
        
        Returns FileValidation with is_supported, is_readable, status
        """
        filename = file.filename.lower()
        file_ext = '.' + filename.split('.')[-1] if '.' in filename else ''
        
        # Check file extension
        is_supported = file_ext in DocumentValidationService.SUPPORTED_EXTENSIONS
        
        # Check file size
        file_size = 0
        try:
            content = await file.read()
            file_size = len(content)
            await file.seek(0)  # Reset file pointer
            
            is_readable = file_size > 0 and file_size <= DocumentValidationService.MAX_FILE_SIZE
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            is_readable = False
            file_size = 0
        
        # Determine status
        if not is_supported:
            status = "FAIL"
            errors = ["Unsupported file type. Only PDF, JPG, PNG are supported."]
        elif not is_readable:
            status = "FAIL"
            errors = ["File is not readable or exceeds size limit."]
        else:
            status = "PASS"
            errors = []
        
        # Determine file type
        if file_ext == '.pdf':
            file_type = "application/pdf"
        elif file_ext in ['.jpg', '.jpeg']:
            file_type = "image/jpeg"
        elif file_ext == '.png':
            file_type = "image/png"
        else:
            file_type = "unknown"
        
        return FileValidation(
            file_type=file_type,
            is_supported=is_supported,
            is_readable=is_readable,
            page_count=0,  # Will be updated after OCR
            status=status,
            errors=errors,
            warnings=[]
        )
