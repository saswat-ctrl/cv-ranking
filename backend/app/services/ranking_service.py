from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.job import Job
from app.models.candidate import Candidate
from app.core.config import settings
from app.core.error_codes import RankingErrorCode
from app.core.exceptions import AppException
from app.services import embedding_service, scoring_service, skills_service

logger = logging.getLogger(__name__)

async def rank_candidates(job_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Rank 2-15 candidates for a job with comprehensive error handling
    """
    start_time = datetime.now()
    warnings = []
    
    # 1. Get job
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .execution_options(populate_existing=True)
    )
    job = result.scalars().first()
    if not job:
        raise AppException(
            message=f"Job {job_id} not found",
            status_code=404,
            code="JOB_NOT_FOUND"
        )
        
    # 2. Get candidates
    result = await db.execute(
        select(Candidate)
        .where(Candidate.job_id == job_id)
        .execution_options(populate_existing=True)
    )
    all_candidates_orm = list(result.scalars().all())
    
    # Convert ORM objects to dicts immediately to avoid lazy loading issues
    all_candidates = []
    for c in all_candidates_orm:
        all_candidates.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "extracted_text": c.extracted_text,
            "embedding": c.embedding,
            "embedding_model": c.embedding_model,
            "is_readable": c.is_readable,
            "parsed_skills": c.parsed_skills,
            "ranking_score": c.ranking_score,
            "semantic_score": c.semantic_score,
            "keyword_score": c.keyword_score,
            "ranking_reasoning": c.ranking_reasoning,
            "orm_object": c  # Keep reference for updates
        })
    
    # Validate candidate count
    if len(all_candidates) < settings.MIN_CANDIDATES:
        raise AppException(
            message=f"Need at least {settings.MIN_CANDIDATES} candidates to rank (current: {len(all_candidates)})",
            status_code=400,
            code=RankingErrorCode.INSUFFICIENT_CANDIDATES.value
        )
        
    if len(all_candidates) > settings.MAX_CANDIDATES:
        raise AppException(
            message=f"Too many candidates ({len(all_candidates)}). Max allowed is {settings.MAX_CANDIDATES}.",
            status_code=400,
            code=RankingErrorCode.TOO_MANY_CANDIDATES.value
        )
    
    # Filter readable candidates
    readable_candidates = [c for c in all_candidates if c["is_readable"]]
    unreadable_count = len(all_candidates) - len(readable_candidates)
    
    if not readable_candidates:
        raise AppException(
            message="No readable candidates found. Please upload valid PDF/DOCX files.",
            status_code=400,
            code=RankingErrorCode.NO_READABLE_CANDIDATES.value
        )
        
    if len(readable_candidates) < settings.MIN_CANDIDATES:
        raise AppException(
            message=f"Need at least {settings.MIN_CANDIDATES} readable candidates to rank (current: {len(readable_candidates)}). {unreadable_count} candidates were unreadable.",
            status_code=400,
            code=RankingErrorCode.INSUFFICIENT_CANDIDATES.value
        )
    
    # 3. JD Quality Check
    jd_text_full = job.extracted_text or ""
    if len(jd_text_full.strip()) < settings.MIN_JD_LENGTH:
        warnings.append({
            "code": RankingErrorCode.JD_TOO_SHORT.value,
            "message": f"JD is very short ({len(jd_text_full)} chars). Rankings may be less accurate."
        })
    
    # Check if JD has any skills mentioned
    skills_db = skills_service.load_skills_database()
    jd_lower = jd_text_full.lower()
    # Simple check for now, could be more sophisticated
    jd_skills_found = [s for s in skills_db if s.lower() in jd_lower]
    
    if len(jd_skills_found) < 3:
        warnings.append({
            "code": RankingErrorCode.JD_NO_SKILLS.value,
            "message": f"JD mentions very few skills ({len(jd_skills_found)}). Consider adding more details."
        })
    
    try:
        # 4. Generate/Get JD Embedding
        if not job.embedding:
            logger.info(f"Generating embedding for job {job_id}")
            jd_emb_bytes, error = embedding_service.generate_embedding(
                jd_text_full, 
                max_length=settings.JD_EMBEDDING_LENGTH
            )
            
            if error:
                # Error is a dict from embedding_service, we need to raise it
                raise AppException(
                    message=error.get("message", "JD embedding failed"),
                    status_code=500,
                    code=error.get("error_code", RankingErrorCode.EMBEDDING_FAILED.value)
                )
                
            job.embedding = jd_emb_bytes
            job.embedding_model = settings.SBERT_MODEL
            await db.commit()
            await db.refresh(job)
        
        jd_embedding = embedding_service.deserialize_embedding(job.embedding)
        
        # 5. Generate/Get Candidate Embeddings (Batch)
        # Identify candidates needing embeddings
        candidates_needing_embedding = []
        texts_to_embed = []
        
        for cand in readable_candidates:
            if not cand["embedding"] or cand["embedding_model"] != settings.SBERT_MODEL:
                candidates_needing_embedding.append(cand)
                texts_to_embed.append(cand["extracted_text"] or "")
        
        if candidates_needing_embedding:
            logger.info(f"Generating embeddings for {len(candidates_needing_embedding)} candidates")
            batch_results = embedding_service.generate_embeddings_batch(texts_to_embed)
            
            for cand, (emb_bytes, error) in zip(candidates_needing_embedding, batch_results):
                if error:
                    logger.warning(f"Failed to embed candidate {cand['id']}: {error}")
                    cand["orm_object"].is_readable = False  # Mark as unreadable if embedding fails
                    cand["orm_object"].ranking_reasoning = f"Embedding failed: {error.get('message', 'Unknown error')}"
                else:
                    cand["orm_object"].embedding = emb_bytes
                    cand["orm_object"].embedding_model = settings.SBERT_MODEL
                    # Update dict as well for next steps
                    cand["embedding"] = emb_bytes
                    cand["embedding_model"] = settings.SBERT_MODEL
            
            await db.commit()
            
        # Re-filter readable candidates (some might have failed embedding)
        readable_candidates = [c for c in all_candidates if c["is_readable"] and c["embedding"]]
        
        if not readable_candidates:
            raise AppException(
                message="All candidates failed processing (embedding generation).",
                status_code=500,
                code=RankingErrorCode.NO_READABLE_CANDIDATES.value
            )

        # 6. Calculate Scores
        # Prepare data for batch operations
        cv_texts = [c["extracted_text"] or "" for c in readable_candidates]
        
        # Batch Keyword Similarity
        keyword_scores = scoring_service.calculate_keyword_similarity_batch(jd_text_full, cv_texts)
        
        for idx, candidate in enumerate(readable_candidates):
            # Semantic Score
            cv_embedding = embedding_service.deserialize_embedding(candidate["embedding"])
            semantic_score = scoring_service.calculate_semantic_similarity(jd_embedding, cv_embedding)
            
            # Keyword Score
            keyword_score = keyword_scores[idx]
            
            # Skill Match
            candidate_skills = candidate["parsed_skills"] or []
            matching_skills = scoring_service.extract_matching_skills(jd_text_full, candidate_skills)
            
            # Calculate skill match ratio (simple heuristic)
            # Assuming ~10 skills is a "full" match for normalization
            skill_match_ratio = min(1.0, len(matching_skills) / 10.0)
            
            # Final Score
            final_score = scoring_service.calculate_final_score(
                semantic_score, 
                keyword_score, 
                skill_match_ratio
            )
            
            # Generate Reasoning
            reasoning = scoring_service.generate_reasoning(
                semantic_score,
                keyword_score,
                matching_skills,
                missing_skills=[s for s in candidate_skills if s not in matching_skills]
            )
            
            # Update Candidate
            candidate_orm = candidate["orm_object"]
            candidate_orm.ranking_score = final_score
            candidate_orm.semantic_score = round(semantic_score * 100, 1)
            candidate_orm.keyword_score = round(keyword_score * 100, 1)
            candidate_orm.ranking_reasoning = str(reasoning) # Store as string representation of dict
            candidate_orm.ranked_at = datetime.now()
            
        # Update Job
        job.ranking_version = settings.RANKING_VERSION
        await db.commit()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "job_id": job_id,
            "total_candidates": len(all_candidates),
            "ranked_count": len(readable_candidates),
            "unreadable_count": unreadable_count,
            "duration_seconds": round(duration, 2),
            "ranking_version": settings.RANKING_VERSION,
            "warnings": warnings
        }
        
    except AppException:
        raise
    except Exception as e:
        logger.error(f"Ranking failed: {e}", exc_info=True)
        raise AppException(
            message=f"Ranking process failed: {str(e)}",
            status_code=500,
            code=RankingErrorCode.EMBEDDING_FAILED.value # Generic fallback
        )
