"""
OCR Service for SwasthyaSarthi Prescription Processing.
Provides OCR functionality using EasyOCR (preferred) with Tesseract fallback.

Priority:
1. EasyOCR - Offline capable, better for medical text
2. Tesseract - Fallback OCR engine
"""

import io
import numpy as np
from typing import Optional, Tuple, List
from PIL import Image
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import EasyOCR
EASYOCR_AVAILABLE = False
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("[OCR] EasyOCR is available")
except ImportError:
    logger.warning("[OCR] EasyOCR not installed, will use Tesseract fallback")

# Try to import Tesseract
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("[OCR] Tesseract is available")
except ImportError:
    logger.warning("[OCR] Tesseract not installed")


class OCRService:
    """
    OCR Service for prescription text extraction.
    Uses EasyOCR with Tesseract fallback.
    """
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR service.
        
        Args:
            languages: List of languages to support. Defaults to ['en', 'hi', 'mr']
        """
        self.languages = languages or ['en', 'hi', 'mr']
        self._reader = None
        self._init_reader()
    
    def _init_reader(self):
        """Initialize EasyOCR reader."""
        if EASYOCR_AVAILABLE:
            try:
                # EasyOCR uses language codes: 'en', 'hi', 'mr'
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=False,  # Use CPU for reliability
                    verbose=False
                )
                logger.info(f"[OCR] EasyOCR initialized with languages: {self.languages}")
            except Exception as e:
                logger.error(f"[OCR] Failed to initialize EasyOCR: {e}")
                self._reader = None
    
    def extract_text(self, image_data: bytes) -> Tuple[str, float]:
        """
        Extract text from prescription image.
        
        Args:
            image_data: Image file bytes
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        # Convert bytes to image
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for EasyOCR
            image_array = np.array(image)
            
        except Exception as e:
            logger.error(f"[OCR] Failed to process image: {e}")
            return "", 0.0
        
        # Try EasyOCR first
        if self._reader is not None:
            try:
                return self._extract_with_easyocr(image_array)
            except Exception as e:
                logger.warning(f"[OCR] EasyOCR extraction failed: {e}")
        
        # Fallback to Tesseract
        if TESSERACT_AVAILABLE:
            try:
                return self._extract_with_tesseract(image)
            except Exception as e:
                logger.warning(f"[OCR] Tesseract extraction failed: {e}")
        
        # Ultimate fallback - return empty
        logger.error("[OCR] All OCR methods failed")
        return "", 0.0
    
    def _extract_with_easyocr(self, image_array: np.ndarray) -> Tuple[str, float]:
        """
        Extract text using EasyOCR.
        
        Args:
            image_array: Image as numpy array
            
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        # Run EasyOCR detection
        results = self._reader.readtext(image_array)
        
        if not results:
            return "", 0.0
        
        # Extract text and confidence
        text_parts = []
        confidences = []
        
        for detection in results:
            # EasyOCR result format: (bbox, text, confidence)
            bbox, text, confidence = detection
            text_parts.append(text.strip())
            confidences.append(confidence)
        
        # Join all text
        full_text = " ".join(text_parts)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        logger.info(f"[OCR] EasyOCR extracted {len(text_parts)} text segments, confidence: {avg_confidence:.2f}")
        
        return full_text, avg_confidence
    
    def _extract_with_tesseract(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text using Tesseract OCR.
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        # Get detailed data including confidence
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang='eng+hin'  # English and Hindi
        )
        
        # Extract text and confidence
        text_parts = []
        confidences = []
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            
            if text:  # Only non-empty text
                text_parts.append(text)
                if conf > 0:  # Tesseract returns -1 for no confidence
                    confidences.append(conf / 100.0)  # Convert to 0-1 range
        
        # Join all text
        full_text = " ".join(text_parts)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        logger.info(f"[OCR] Tesseract extracted {len(text_parts)} text segments, confidence: {avg_confidence:.2f}")
        
        return full_text, avg_confidence
    
    def extract_with_fallback(self, image_data: bytes) -> dict:
        """
        Extract text with detailed metadata about the extraction process.
        
        Args:
            image_data: Image file bytes
            
        Returns:
            Dictionary with extracted text and metadata
        """
        result = {
            "text": "",
            "confidence": 0.0,
            "method": "none",
            "success": False,
            "error": None
        }
        
        # Try EasyOCR first
        if self._reader is not None:
            try:
                text, confidence = self.extract_text(image_data)
                if text.strip():
                    result["text"] = text
                    result["confidence"] = confidence
                    result["method"] = "easyocr"
                    result["success"] = True
                    return result
            except Exception as e:
                result["error"] = f"EasyOCR error: {str(e)}"
                logger.warning(f"[OCR] EasyOCR failed: {e}")
        
        # Fallback to Tesseract
        if TESSERACT_AVAILABLE:
            try:
                image = Image.open(io.BytesIO(image_data))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                text, confidence = self._extract_with_tesseract(image)
                if text.strip():
                    result["text"] = text
                    result["confidence"] = confidence
                    result["method"] = "tesseract"
                    result["success"] = True
                    return result
            except Exception as e:
                result["error"] = f"Tesseract error: {str(e)}"
                logger.warning(f"[OCR] Tesseract failed: {e}")
        
        # All methods failed
        result["error"] = result.get("error", "All OCR methods failed")
        return result


# Global instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service instance."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(languages=['en', 'hi', 'mr'])
    return _ocr_service


def extract_prescription_text(image_data: bytes) -> dict:
    """
    Convenience function to extract prescription text.
    
    Args:
        image_data: Image file bytes
        
    Returns:
        Dictionary with extraction results
    """
    service = get_ocr_service()
    return service.extract_with_fallback(image_data)


# Export
__all__ = [
    'OCRService',
    'get_ocr_service',
    'extract_prescription_text',
    'EASYOCR_AVAILABLE',
    'TESSERACT_AVAILABLE'
]
