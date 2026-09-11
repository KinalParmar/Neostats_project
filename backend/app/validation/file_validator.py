from fastapi import UploadFile, HTTPException
from typing import Tuple, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import io
import os


class FileValidator:
    """Validates uploaded files before processing"""
    
    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
    MAX_PAGES = 3
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    async def validate_file(file: UploadFile) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate uploaded file.
        Returns (is_valid, validation_result)
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_type": None,
            "page_count": None,
            "file_size": None,
            "filename": file.filename
        }
        
        try:
            # Read file content
            content = await file.read()
            result["file_size"] = len(content)
            
            # Reset file pointer
            await file.seek(0)
            
            # Check if file is empty
            if len(content) == 0:
                result["valid"] = False
                result["errors"].append("File is empty")
                return result["valid"], result
            
            # Check file size
            if len(content) > FileValidator.MAX_FILE_SIZE:
                result["valid"] = False
                result["errors"].append(f"File too large. Maximum size: {FileValidator.MAX_FILE_SIZE / (1024*1024)}MB")
                return result["valid"], result
            
            # Validate extension
            if not file.filename:
                result["valid"] = False
                result["errors"].append("No filename provided")
                return result["valid"], result
            
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in FileValidator.ALLOWED_EXTENSIONS:
                result["valid"] = False
                result["errors"].append(f"Invalid file extension: {ext}. Allowed: .pdf, .jpg, .jpeg, .png")
                return result["valid"], result
            
            # Determine file type and validate based on extension
            if ext == ".pdf":
                result["file_type"] = "application/pdf"
                try:
                    doc = fitz.open(stream=content, filetype="pdf")
                    page_count = len(doc)
                    result["page_count"] = page_count
                    doc.close()
                    
                    if page_count > FileValidator.MAX_PAGES:
                        result["valid"] = False
                        result["errors"].append(f"PDF has {page_count} pages. Maximum allowed: {FileValidator.MAX_PAGES}")
                        return result["valid"], result
                    
                    if page_count == 0:
                        result["valid"] = False
                        result["errors"].append("PDF has no pages")
                        return result["valid"], result
                        
                except Exception as e:
                    result["valid"] = False
                    result["errors"].append(f"Failed to read PDF: {str(e)}")
                    return result["valid"], result
            
            elif ext in [".jpg", ".jpeg", ".png"]:
                # Determine MIME type
                if ext == ".png":
                    result["file_type"] = "image/png"
                else:
                    result["file_type"] = "image/jpeg"
                
                # Verify it's a valid image
                try:
                    img = Image.open(io.BytesIO(content))
                    img.verify()
                    # Reopen for further processing
                    img = Image.open(io.BytesIO(content))
                    result["page_count"] = 1  # Images count as 1 page
                except Exception as e:
                    result["valid"] = False
                    result["errors"].append(f"Failed to read image: {str(e)}")
                    return result["valid"], result
            
            return result["valid"], result
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Validation error: {str(e)}")
            return result["valid"], result
