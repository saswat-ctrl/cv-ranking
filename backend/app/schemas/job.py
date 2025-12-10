from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.job import JobStatus

class JobBase(BaseModel):
    title: str
    description: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None

class JobResponse(JobBase):
    id: UUID4
    user_id: UUID4
    file_url: str
    extracted_text: Optional[str] = None
    extraction_status: str
    extraction_error: Optional[str] = None
    extraction_duration: Optional[float] = None
    status: JobStatus
    created_at: datetime

    class Config:
        from_attributes = True
