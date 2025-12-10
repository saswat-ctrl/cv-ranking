
import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, LargeBinary
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ranking_jobs.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cv_file_url = Column(String, nullable=False)
    
    # Extraction fields (from migration 005)
    extracted_text = Column(Text, nullable=True)
    extraction_status = Column(String(20), nullable=False, server_default='pending')
    extraction_error = Column(Text, nullable=True)
    extraction_duration = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    
    # Parsing fields (from migration 005)
    parsed_name = Column(String(255), nullable=True)
    parsed_email = Column(String(255), nullable=True)
    parsed_phone = Column(String(50), nullable=True)
    parsed_skills = Column(postgresql.JSON(astext_type=Text()), nullable=True)
    
    # Legacy/Phase 1 fields (mapped or deprecated)
    # cv_text_content was renamed/replaced by extracted_text in migration logic but we should align model
    # match_score and reasoning exist
    match_score = Column(Integer, nullable=True)
    reasoning = Column(Text, nullable=True, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Ranking fields
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String, nullable=True)
    ranking_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    ranking_reasoning = Column(Text, nullable=True)
    ranked_at = Column(DateTime(timezone=True), nullable=True)
    is_readable = Column(Boolean, default=True)
    user_score = Column(Float, nullable=True)  # Manual score set by user (0-100)
    
    # Relationships
    job = relationship("Job", back_populates="candidates")
