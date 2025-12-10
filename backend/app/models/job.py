import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Float, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class JobStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    # Legacy statuses to prevent enum errors if old data exists
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "ranking_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Map model attributes to DB columns
    title = Column("job_title", String, nullable=True)
    file_url = Column("jd_file_url", String, nullable=False)
    
    # New fields from migration 004 (column names match attribute names)
    extracted_text = Column(Text, nullable=True)
    extraction_status = Column(String, default="pending")
    extraction_error = Column(Text, nullable=True)
    extraction_duration = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)
    
    # Legacy field (keep for compatibility but don't use)
    jd_text_content = Column(Text, nullable=True)
    
    status = Column(Enum(JobStatus), default=JobStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Ranking fields
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String, nullable=True)
    ranking_version = Column(String, nullable=True)
    
    # Relationships
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")

    user = relationship("User", backref="jobs")
