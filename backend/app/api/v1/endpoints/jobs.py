from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, asc
from typing import List, Optional
import shutil
import os
import tempfile
from datetime import datetime
import uuid
from fastapi.responses import RedirectResponse

from app.api import deps
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.candidate import Candidate
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.schemas.candidate import CandidateCreate, CandidateResponse
from app.schemas.candidate import CandidateCreate, CandidateResponse
from app.services.storage_service import get_storage_provider
from app.core.exceptions import FileError
from app.services.extraction_service import extract_text
from app.services.parsing_service import parse_resume
from app.services.ranking_service import rank_candidates
from app.core.config import settings

router = APIRouter()

@router.post("", response_model=JobResponse)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new job with JD text.
    """
    # Create Job record
    db_job = Job(
        title=job_in.title,
        user_id=current_user.id,
        file_url="text_entry", # Placeholder for text-only jobs
        extracted_text=job_in.description,
        extraction_status="completed",
        extraction_error=None,
        extraction_duration=0,
        file_type="text/plain",
        file_size=len(job_in.description) if job_in.description else 0,
        status=JobStatus.OPEN
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    return db_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a job and all associated candidates.
    """
    # Verify job exists and belongs to user
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete the job
    await db.delete(job)
    await db.commit()
    return None


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get job details.
    """
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_in: JobUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a job.
    """
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = job_in.dict(exclude_unset=True)
    
    # Map 'description' to 'extracted_text' because that's where we store the JD
    if "description" in update_data:
        update_data["extracted_text"] = update_data.pop("description")

    for field, value in update_data.items():
        setattr(job, field, value)

    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List all jobs"""
    result = await db.execute(
        select(Job)
        .where(Job.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    return jobs


@router.post("/{job_id}/candidates", response_model=CandidateResponse)
async def upload_candidate(
    job_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Upload a candidate CV for a job.
    Synchronously extracts text and parses resume data.
    """
    # Verify job exists and belongs to user
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Check candidate limit
    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id)
    )
    current_count = len(result.scalars().all()) # Inefficient but simple for now
    
    if current_count >= settings.MAX_CANDIDATES:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum candidate limit ({settings.MAX_CANDIDATES}) reached for this job."
        )
        
    # 1. Validate File
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # Check file size (approximate, as we can't easily get size from UploadFile without reading)
    # But we can check content-length header if available, or just proceed.
    # For now, we'll trust the client or check after save if needed.
    
    # 2. Upload File & Extract
    temp_path = None
    try:
        # Save to temp file first for extraction
        file_ext = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        # Reset file pointer for upload
        await file.seek(0)
        
        # Upload to storage
        storage = get_storage_provider()
        file_url = await storage.upload(file, "candidates")
        
        # 3. Extract text & Parse (Synchronous)
        start_time = datetime.now()
        extracted_text, extraction_error = await extract_text(temp_path, file.content_type)
        
        parsed_data = {}
        if extracted_text and not extraction_error:
            parsed_data = await parse_resume(extracted_text)
            
        duration = (datetime.now() - start_time).total_seconds()

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")
        
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Check for duplicate by email (if email was parsed)
    candidate_email = parsed_data.get("email") or ""
    if candidate_email:
        result = await db.execute(
            select(Candidate).where(
                Candidate.job_id == job_id,
                Candidate.email == candidate_email
            )
        )
        existing_candidate = result.scalars().first()
        if existing_candidate:
            raise HTTPException(
                status_code=400,
                detail=f"Candidate with email {candidate_email} already exists for this job."
            )
    
    # 3. Create Candidate record
    db_candidate = Candidate(
        job_id=job_id,
        name=parsed_data.get("name") or "Unknown Candidate",
        email=parsed_data.get("email") or "",
        parsed_phone=parsed_data.get("phone"),
        cv_file_url=file_url,
        extracted_text=extracted_text,
        parsed_skills=parsed_data.get("skills", []),
        extraction_status="completed" if not extraction_error else "failed",
        extraction_error=extraction_error,
        extraction_duration=duration,
        file_type=file.content_type,
        file_size=file.size
    )
    
    db.add(db_candidate)
    await db.commit()
    await db.refresh(db_candidate)
    
    return db_candidate


@router.get("/{job_id}/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    List candidates for a job.
    """
    # Verify job exists and belongs to user
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id)
    )
    return result.scalars().all()
    count_query = select(func.count()).select_from(Candidate).where(Candidate.job_id == job_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    # Return paginated response
    return PaginatedResponse.create(
        items=candidates,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{job_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    job_id: str,
    candidate_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get candidate details"""
    # Verify job exists
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.job_id == job_id)
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    return candidate


@router.post("/{job_id}/rank")
async def rank_job_candidates(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Rank candidates for a job.
    Triggers the ranking process (SBERT embedding + scoring).
    """
    # Verify job exists
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Run ranking
    result = await rank_candidates(job_id, db)
    
    return result


@router.get("/{job_id}/candidates/{candidate_id}/download")
async def download_candidate_cv(
    job_id: str,
    candidate_id: str,
    inline: bool = False,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Download or view a candidate's CV.
    """
    # Verify job ownership
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.job_id == job_id)
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate.cv_file_url:
        raise HTTPException(status_code=404, detail="CV file not found record")

    # Get storage provider
    storage = get_storage_provider()
    
    try:
        # Generate download URL (Presigned URL for S3, or Stream URL for Local)
        download_url = await storage.generate_download_url(
            candidate.cv_file_url, 
            original_filename=f"{candidate.name.replace(' ', '_')}_CV{os.path.splitext(candidate.cv_file_url)[1]}"
        )
        
        # Redirect the client to the download URL
        # For S3: It's a presigned URL, client downloads directly
        # For Local: It's a stream endpoint on our API, client follows redirect with Auth headers
        return RedirectResponse(url=download_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download link: {str(e)}")


@router.post("/{job_id}/import_candidates")
async def import_candidates_from_job(
    job_id: str,
    request_data: dict,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Import candidates from another job to this job.
    Request body: {"source_job_id": "uuid", "candidate_ids": ["uuid1", "uuid2"]}
    """
    source_job_id = request_data.get("source_job_id")
    candidate_ids = request_data.get("candidate_ids", [])
    
    if not source_job_id or not candidate_ids:
        raise HTTPException(status_code=400, detail="source_job_id and candidate_ids are required")
    
    # Verify target job exists and belongs to user
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    target_job = result.scalars().first()
    if not target_job:
        raise HTTPException(status_code=404, detail="Target job not found")
    
    # Verify source job exists and belongs to user
    result = await db.execute(
        select(Job).where(Job.id == source_job_id, Job.user_id == current_user.id)
    )
    source_job = result.scalars().first()
    if not source_job:
        raise HTTPException(status_code=404, detail="Source job not found")
    
    # Check current candidate count in target job
    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id)
    )
    current_count = len(result.scalars().all())
    
    if current_count >= settings.MAX_CANDIDATES:
        raise HTTPException(
            status_code=400,
            detail=f"Target job already has maximum candidates ({settings.MAX_CANDIDATES})"
        )
    
    # Limit import to avoid exceeding max
    available_slots = settings.MAX_CANDIDATES - current_count
    if len(candidate_ids) > available_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Can only import {available_slots} more candidates (current: {current_count}, max: {settings.MAX_CANDIDATES})"
        )
    
    # Fetch candidates from source job
    result = await db.execute(
        select(Candidate).where(
            Candidate.id.in_(candidate_ids),
            Candidate.job_id == source_job_id
        )
    )
    source_candidates = result.scalars().all()
    
    if len(source_candidates) != len(candidate_ids):
        raise HTTPException(status_code=404, detail="Some candidates not found in source job")
    
    # Get existing emails in target job for duplicate check
    result = await db.execute(
        select(Candidate.email).where(Candidate.job_id == job_id)
    )
    existing_emails = {email for (email,) in result.fetchall() if email}
    
    imported_count = 0
    skipped_count = 0
    
    for source_candidate in source_candidates:
        # Skip if email already exists in target job (duplicate)
        if source_candidate.email and source_candidate.email in existing_emails:
            skipped_count += 1
            continue
        
        # Create new candidate in target job (copy all data)
        new_candidate = Candidate(
            job_id=job_id,
            name=source_candidate.name,
            email=source_candidate.email,
            parsed_phone=source_candidate.parsed_phone,
            cv_file_url=source_candidate.cv_file_url,  # Reference same file
            extracted_text=source_candidate.extracted_text,
            parsed_skills=source_candidate.parsed_skills,
            extraction_status=source_candidate.extraction_status,
            extraction_error=source_candidate.extraction_error,
            extraction_duration=source_candidate.extraction_duration,
            file_type=source_candidate.file_type,
            file_size=source_candidate.file_size,
            is_readable=source_candidate.is_readable,
            # Don't copy ranking data - will be re-ranked for new job
        )
        
        db.add(new_candidate)
        imported_count += 1
    
    await db.commit()
    
    return {
        "imported": imported_count,
        "skipped": skipped_count,
        "message": f"Imported {imported_count} candidates, skipped {skipped_count} duplicates"
    }


from typing import Optional
from pydantic import BaseModel

class CandidateUpdate(BaseModel):
    user_score: Optional[float] = None


from app.schemas.candidate import CandidateResponse

@router.patch("/{job_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    job_id: str,
    candidate_id: str,
    update_data: CandidateUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update candidate fields (currently supports user_score).
    """
    # Verify job ownership
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.job_id == job_id)
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Update user_score if provided
    if update_data.user_score is not None:
        if update_data.user_score < 0 or update_data.user_score > 100:
            raise HTTPException(status_code=400, detail="User score must be between 0 and 100")
        candidate.user_score = update_data.user_score

    await db.commit()
    await db.refresh(candidate)
    
    return candidate


@router.delete("/{job_id}/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    job_id: str,
    candidate_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a candidate from a job.
    """
    # Verify job ownership
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.job_id == job_id)
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Delete the candidate
    await db.delete(candidate)
    await db.commit()
    return None
