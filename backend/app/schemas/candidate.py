from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None

class CandidateCreate(CandidateBase):
    job_id: str

class CandidateResponse(CandidateBase):
    id: UUID4
    job_id: UUID4
    cv_file_url: str
    extracted_text: Optional[str] = None
    parsed_skills: Optional[List[str]] = None
    extraction_status: str
    extraction_error: Optional[str] = None
    extraction_duration: Optional[float] = None
    match_score: Optional[float] = None
    reasoning: Optional[str] = None
    
    # Ranking fields
    ranking_score: Optional[float] = None
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    ranking_reasoning: Optional[str] = None
    is_readable: bool = True
    ranked_at: Optional[datetime] = None
    user_score: Optional[float] = None
    
    created_at: datetime

    class Config:
        from_attributes = True
