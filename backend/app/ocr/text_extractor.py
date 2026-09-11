from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io
import easyocr
import numpy as np
from app.core.config import settings


class TextExtractor:
    """Extracts text from PDFs and images using native extraction or OCR"""
    
    def __init__(self):
        # Configure Tesseract path if provided
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
        
        # Initialize EasyOCR reader (lazy load)
        self._easyocr_reader = None
    
    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self._easyocr_reader is None:
            self._easyocr_reader = easyocr.Reader(['en'])
        return self._easyocr_reader
    
    def extract_from_pdf(self, content: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extract text from PDF.
        First tries native text extraction, falls back to OCR if needed.
        Returns (pages_data, extraction_method)
        """
        pages_data = []
        extraction_method = "native"
        
        try:
            # Try native text extraction with pdfplumber first
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    if text and text.strip():
                        pages_data.append({
                            "page_number": page_num,
                            "text": text,
                            "extraction_method": "native"
                        })
                    else:
                        # No text found, might be scanned - fall back to OCR
                        extraction_method = "ocr"
                        break
            
            # If we got all pages with native extraction, return
            if extraction_method == "native" and len(pages_data) > 0:
                return pages_data, extraction_method
            
            # Fall back to OCR for scanned PDFs
            return self._ocr_pdf(content), "ocr"
            
        except Exception as e:
            # If native extraction fails, try OCR
            try:
                return self._ocr_pdf(content), "ocr"
            except Exception as ocr_error:
                raise Exception(f"Native extraction failed: {str(e)}. OCR also failed: {str(ocr_error)}")
    
    def _ocr_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        """OCR a PDF by converting pages to images"""
        pages_data = []
        
        doc = fitz.open(stream=content, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Convert page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Try EasyOCR first (no external installation required)
            text = None
            method = "ocr"
            try:
                text = self._ocr_with_easyocr(img)
                if text and len(text.strip()) >= 10:
                    method = "ocr_easyocr"
            except Exception as e:
                print(f"EasyOCR failed for page {page_num + 1}: {e}")
            
            # Fall back to Tesseract if EasyOCR fails or gives poor results
            if not text or len(text.strip()) < 10:
                try:
                    text = self._ocr_with_tesseract(img)
                    method = "ocr_tesseract"
                except Exception as e:
                    print(f"Tesseract failed for page {page_num + 1}: {e}")
                    text = f"OCR failed for page {page_num + 1}"
            
            pages_data.append({
                "page_number": page_num + 1,
                "text": text,
                "extraction_method": method
            })
        
        doc.close()
        return pages_data
    
    def extract_from_image(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from image (JPG, PNG) using OCR.
        Returns list with single page data.
        """
        img = Image.open(io.BytesIO(content))
        
        # Try EasyOCR first (no external installation required)
        try:
            text = self._ocr_with_easyocr(img)
            if text and len(text.strip()) >= 10:
                return [{
                    "page_number": 1,
                    "text": text,
                    "extraction_method": "ocr_easyocr"
                }]
        except Exception as e:
            print(f"EasyOCR failed: {e}")
        
        # Fall back to Tesseract if EasyOCR fails
        try:
            text = self._ocr_with_tesseract(img)
            return [{
                "page_number": 1,
                "text": text,
                "extraction_method": "ocr_tesseract"
            }]
        except Exception as e:
            raise Exception(f"All OCR methods failed. EasyOCR error: {str(e)}. Tesseract error: {str(e)}")
    
    def _ocr_with_tesseract(self, img: Image.Image) -> str:
        """Extract text using Tesseract OCR"""
        try:
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            # If Tesseract is not installed, raise a clear error
            if "tesseract is not installed" in str(e).lower() or "not in your path" in str(e).lower():
                raise Exception("Tesseract OCR is not installed. Please install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki")
            raise Exception(f"Tesseract OCR failed: {str(e)}")
    
    def _ocr_with_easyocr(self, img: Image.Image) -> str:
        """Extract text using EasyOCR (fallback)"""
        try:
            # Convert PIL image to numpy array
            img_array = np.array(img)
            
            # Run EasyOCR
            results = self.easyocr_reader.readtext(img_array)
            
            # Combine all detected text
            text_lines = [result[1] for result in results]
            return "\n".join(text_lines)
        except Exception as e:
            raise Exception(f"EasyOCR failed: {str(e)}")
