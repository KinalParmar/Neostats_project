from typing import List, Dict, Any, Tuple
import io
import logging
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR and text extraction from documents"""
    
    def __init__(self):
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            self.easyocr_available = True
            logger.info("EasyOCR initialized (CPU mode)")
        except ImportError:
            self.easyocr_available = False
            logger.warning("EasyOCR not available - using native text extraction only")
    
    def extract_from_pdf(self, content: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extract text from PDF
        Returns (pages_data, extraction_method)
        """
        pages_data = []
        
        # Try native text extraction first
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page_num, page in enumerate(pdf.pages[:3], start=1):  # Max 3 pages
                    text = page.extract_text()
                    if text:
                        pages_data.append({
                            "page_number": page_num,
                            "text": text
                        })
            
            if pages_data:
                return pages_data, "native"
        except Exception as e:
            logger.error(f"Native PDF extraction failed: {e}")
        
        # Fall back to OCR if available
        if self.easyocr_available:
            try:
                pages_data = self._ocr_pdf(content)
                return pages_data, "ocr"
            except Exception as e:
                logger.error(f"OCR PDF extraction failed: {e}")
        
        return pages_data, "none"
    
    def extract_from_image(self, content: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extract text from image (JPG, PNG)
        Returns (pages_data, extraction_method)
        """
        pages_data = []
        
        if self.easyocr_available:
            try:
                image = Image.open(io.BytesIO(content))
                result = self.easyocr_reader.readtext(image)
                text = "\n".join([item[1] for item in result])
                
                if text:
                    pages_data.append({
                        "page_number": 1,
                        "text": text
                    })
                
                return pages_data, "ocr"
            except Exception as e:
                logger.error(f"OCR image extraction failed: {e}")
        
        return pages_data, "none"
    
    def _ocr_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        """OCR PDF pages using EasyOCR"""
        pages_data = []
        
        try:
            import fitz  # PyMuPDF
            import tempfile
            import os
            
            # Save bytes to temp file for PyMuPDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                doc = fitz.open(tmp_path)
                
                for page_num in range(min(len(doc), 3)):  # Max 3 pages
                    page = doc[page_num]
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))
                    
                    result = self.easyocr_reader.readtext(image)
                    text = "\n".join([item[1] for item in result])
                    
                    if text:
                        pages_data.append({
                            "page_number": page_num + 1,
                            "text": text
                        })
                
                doc.close()
            finally:
                os.unlink(tmp_path)
                
        except ImportError:
            logger.error("PyMuPDF not available for PDF OCR")
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
        
        return pages_data
