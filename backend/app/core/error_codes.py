from enum import Enum

class RankingErrorCode(str, Enum):
    """Structured error codes for ranking failures"""
    
    # Extraction errors
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    OCR_FAILED = "OCR_FAILED"
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    
    # Embedding errors
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    EMBEDDING_DESERIALIZATION_FAILED = "EMBEDDING_DESERIALIZATION_FAILED"
    SBERT_MODEL_ERROR = "SBERT_MODEL_ERROR"
    
    # Ranking errors
    INSUFFICIENT_CANDIDATES = "INSUFFICIENT_CANDIDATES"
    TOO_MANY_CANDIDATES = "TOO_MANY_CANDIDATES"
    NO_READABLE_CANDIDATES = "NO_READABLE_CANDIDATES"
    
    # Data quality warnings
    JD_TOO_SHORT = "JD_TOO_SHORT"
    JD_NO_SKILLS = "JD_NO_SKILLS"
    CV_NO_SKILLS = "CV_NO_SKILLS"

def create_error_response(code: RankingErrorCode, message: str, details: dict = None) -> dict:
    """Create structured error response"""
    return {
        "error_code": code.value,
        "message": message,
        "details": details or {}
    }
