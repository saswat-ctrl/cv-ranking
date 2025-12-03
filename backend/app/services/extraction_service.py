"""
Text Extraction Service
Handles extraction of text from PDF, DOCX, and image files using open-source tools.
"""

import os
import logging
from typing import Optional, Tuple
import pymupdf  # PyMuPDF
from docx import Document
# from paddleocr import PaddleOCR
import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Initialize PaddleOCR (lazy load on first use)
_paddle_ocr = None

def get_paddle_ocr():
    """Lazy load PaddleOCR to avoid startup overhead"""
    # global _paddle_ocr
    # if _paddle_ocr is None:
    #     _paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
    # return _paddle_ocr
    return None


async def extract_text_from_pdf(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Extract text from PDF using PyMuPDF.
    Falls back to OCR if text extraction yields minimal content.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    try:
        doc = pymupdf.open(file_path)
        text = ""
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text += page_text + "\n"
        
        doc.close()
        
        # If extracted text is too short, might be scanned PDF
        if len(text.strip()) < 100:
            logger.warning(f"PDF {file_path} has minimal text ({len(text)} chars), attempting OCR")
            return await extract_text_from_scanned_pdf(file_path)
        
        logger.info(f"Successfully extracted {len(text)} characters from PDF {file_path}")
        return text.strip(), None
        
    except Exception as e:
        error_msg = f"PyMuPDF extraction failed: {str(e)}"
        logger.error(error_msg)
        return "", error_msg


async def extract_text_from_scanned_pdf(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Extract text from scanned PDF using Tesseract OCR.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    try:
        # Convert PDF pages to images
        doc = pymupdf.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Use Tesseract OCR
            try:
                image = Image.open(io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
            except Exception as tesseract_error:
                logger.error(f"Tesseract failed on page {page_num}: {tesseract_error}")
                continue
        
        doc.close()
        
        if len(text.strip()) < 50:
            error_msg = "OCR extraction yielded minimal text"
            logger.warning(error_msg)
            return text.strip(), error_msg
        
        logger.info(f"Successfully extracted {len(text)} characters from scanned PDF {file_path}")
        return text.strip(), None
        
    except Exception as e:
        error_msg = f"Scanned PDF extraction failed: {str(e)}"
        logger.error(error_msg)
        return "", error_msg


async def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using PaddleOCR.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        Extracted text
    """
    # ocr = get_paddle_ocr()
    logger.warning("PaddleOCR is temporarily disabled due to Docker ARM64 compatibility issues.")
    return ""
    
    # Save bytes to temp file (PaddleOCR requires file path)
    # import tempfile
    # with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
    #     tmp.write(image_bytes)
    #     tmp_path = tmp.name
    
    # try:
    #     result = ocr.ocr(tmp_path, cls=True)
        
    #     if not result or not result[0]:
    #         return ""
        
    #     # Extract text from OCR result
    #     text_lines = []
    #     for line in result[0]:
    #         if len(line) >= 2:
    #             text_lines.append(line[1][0])  # line[1][0] is the text, line[1][1] is confidence
        
    #     return "\n".join(text_lines)
    # finally:
    #     # Clean up temp file
    #     if os.path.exists(tmp_path):
    #         os.remove(tmp_path)


async def extract_text_from_image(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Extract text from image file using Tesseract OCR.
    
    Args:
        file_path: Path to image file (JPG, PNG, etc.)
        
    Returns:
        Tuple of (extracted_text, error_message, is_readable)
    """
    extracted_text = ""
    error_msg = None
    try:
        # Use Tesseract for image OCR
        image = Image.open(file_path)
        extracted_text = pytesseract.image_to_string(image)
        
        if len(extracted_text.strip()) < 50:
            error_msg = "Image OCR extraction yielded minimal text"
            logger.warning(error_msg)
        
        logger.info(f"Successfully extracted {len(extracted_text)} characters from image {file_path}")
        
    except Exception as e:
        error_msg = f"Image extraction failed: {str(e)}"
        logger.error(error_msg)
        return "", error_msg
    
    return extracted_text.strip(), error_msg


async def extract_text_from_docx(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Extract text from DOCX file using python-docx.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    try:
        doc = Document(file_path)
        
        # Extract text from paragraphs
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        
        # Extract text from tables
        table_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    table_text.append(" | ".join(row_text))
        
        # Combine all text
        text = "\n".join(paragraphs)
        if table_text:
            text += "\n\nTables:\n" + "\n".join(table_text)
        
        if len(text.strip()) < 100:
            error_msg = "DOCX extraction yielded minimal text"
            logger.warning(error_msg)
            return text.strip(), error_msg
        
        logger.info(f"Successfully extracted {len(text)} characters from DOCX {file_path}")
        return text.strip(), None
        
    except Exception as e:
        error_msg = f"DOCX extraction failed: {str(e)}"
        logger.error(error_msg)
        return "", error_msg


async def extract_text(file_path: str, mime_type: str) -> Tuple[str, Optional[str]]:
    """
    Main extraction function that routes to appropriate extractor based on file type.
    
    Args:
        file_path: Path to file
        mime_type: MIME type of file
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    logger.info(f"Extracting text from {file_path} (type: {mime_type})")
    
    if mime_type == "application/pdf":
        return await extract_text_from_pdf(file_path)
    elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        return await extract_text_from_docx(file_path)
    elif mime_type.startswith("image/"):
        return await extract_text_from_image(file_path)
    else:
        error_msg = f"Unsupported file type: {mime_type}"
        logger.error(error_msg)
        return "", error_msg
