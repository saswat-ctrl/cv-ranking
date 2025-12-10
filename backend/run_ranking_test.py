#!/usr/bin/env python3
"""
Standalone Manual Ranking Test Script
Uses SQLite for simplicity (no Postgres required)
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.extraction_service import extract_text
from app.services.parsing_service import parse_resume
from app.services.ranking_service import rank_candidates
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User  # Import to resolve SQLAlchemy relationships
from app.db.session import Base

# SQLite database for testing
TEST_DB_PATH = "test_ranking.db"
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

TEST_DOCS_DIR = Path(__file__).parent / "test_documents"
JD_FILE = "Product Manager JD copy.pdf"
CV_FILES = [
    "Anish Sinha CV'25.pdf",
    "Saswat_Ray_PM4000.pdf",
    "Screenshot 2025-11-28 at 1.23.46 PM.jpeg",
    "example-university-student-CV-compressed.pdf"
]

def setup_database(engine):
    """Create all tables"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("✅ Database initialized")

def run_manual_ranking():
    # Setup database
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    
    setup_database(engine)
    
    db = SessionLocal()
    try:
        print(f"\n{'='*100}")
        print(f"🧪 MANUAL RANKING TEST")
        print(f"{'='*100}\n")
        
        # 0. Create Test User
        print(f"[0/4] Creating test user...")
        test_user = User(
            email="test@example.com",
            hashed_password="dummy_hash",
            name="Test User"
        )
        db.add(test_user)
        db.flush()
        print(f"✅ Test user created (ID: {test_user.id})\n")
        
        # 1. Create Job & Extract JD
        print(f"[1/4] Processing JD: {JD_FILE}")
        jd_path = TEST_DOCS_DIR / JD_FILE
        
        if not jd_path.exists():
            print(f"❌ JD file not found: {jd_path}")
            return
        
        with open(jd_path, "rb") as f:
            jd_bytes = f.read()
        
        # Save to temp file for extraction
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(jd_bytes)
            jd_temp_path = tmp.name
        
        jd_text, jd_error = asyncio.run(extract_text(jd_temp_path, "application/pdf"))
        os.remove(jd_temp_path)
        
        if jd_error:
            print(f"❌ JD extraction failed: {jd_error}")
            return
        
        job = Job(
            user_id=test_user.id,
            title="Test Product Manager",
            file_url=f"file://{jd_path}",
            extracted_text=jd_text
        )
        db.add(job)
        db.flush()
        print(f"✅ Job Created (ID: {job.id})")
        print(f"   Extracted {len(job.extracted_text)} chars\n")

        # 2. Process CVs
        print(f"[2/4] Processing {len(CV_FILES)} CVs...")
        for cv_file in CV_FILES:
            cv_path = TEST_DOCS_DIR / cv_file
            print(f"   → Processing {cv_file}...", end=" ", flush=True)
            
            if not cv_path.exists():
                print(f"❌ Not found")
                continue
            
            with open(cv_path, "rb") as f:
                cv_bytes = f.read()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=cv_path.suffix) as tmp:
                tmp.write(cv_bytes)
                cv_temp_path = tmp.name
            
            # Extract
            mime_type = "image/jpeg" if cv_file.endswith(".jpeg") else "application/pdf"
            extracted_text, extract_error = asyncio.run(extract_text(cv_temp_path, mime_type))
            os.remove(cv_temp_path)
            
            # Determine readability
            is_readable = len(extracted_text.strip()) >= 100
            
            # Parse
            parse_result = {}
            if extracted_text and not extract_error:
                parse_result = asyncio.run(parse_resume(extracted_text))
            
            # Create Candidate
            candidate = Candidate(
                job_id=job.id,
                name=parse_result.get("name") or "Unknown",
                email=parse_result.get("email") or "unknown@example.com",
                cv_file_url=f"file://{cv_path}",
                extracted_text=extracted_text,
                is_readable=is_readable,
                parsed_skills=parse_result.get("skills", []),
                extraction_status="completed" if not extract_error else "failed",
                extraction_error=extract_error
            )
            db.add(candidate)
            print(f"✅ (Readable: {candidate.is_readable})")
        
        db.flush()
        
        # 3. Rank Candidates
        print(f"\n[3/4] Ranking Candidates...")
        print(f"DEBUG: job.id = {job.id}, type = {type(job.id)}")
        rank_result = asyncio.run(rank_candidates(job.id, db))
        
        if not rank_result.get("success"):
            print(f"❌ Ranking Failed: {rank_result.get('message', 'Unknown error')}")
            if "error_code" in rank_result:
                print(f"   Error Code: {rank_result['error_code']}")
            return
        
        print(f"✅ Ranking Complete!")
        print(f"   Ranked: {rank_result['ranked_count']}/{rank_result['total_candidates']}")
        print(f"   Duration: {rank_result['duration_seconds']}s")
        if rank_result.get('warnings'):
            for warning in rank_result['warnings']:
                print(f"   ⚠️  {warning['message']}")

        # 4. Display Results
        print(f"\n[4/4] 🏆 RANKING RESULTS")
        print("="*100)
        print(f"{'Rank':<5} | {'Score':<6} | {'Name':<30} | {'Semantic':<8} | {'Keyword':<8} | {'Skills':<6}")
        print("-" * 100)
        
        candidates = db.query(Candidate).filter(Candidate.job_id == job.id).order_by(Candidate.ranking_score.desc()).all()
        
        for idx, c in enumerate(candidates):
            if not c.ranking_score:
                continue
            
            score = f"{c.ranking_score:.1f}"
            sem = f"{c.semantic_score:.1f}" if c.semantic_score else "N/A"
            key = f"{c.keyword_score:.1f}" if c.keyword_score else "N/A"
            skills = len(c.parsed_skills) if c.parsed_skills else 0
            
            print(f"#{idx+1:<4} | {score:<6} | {c.name[:30]:<30} | {sem:<8} | {key:<8} | {skills:<6}")
            
            # Print Reasoning (truncated)
            if c.ranking_reasoning:
                reasoning_preview = c.ranking_reasoning[:150] + "..." if len(c.ranking_reasoning) > 150 else c.ranking_reasoning
                print(f"      💡 {reasoning_preview}")
            print("-" * 100)

        unreadable = [c for c in candidates if not c.is_readable]
        if unreadable:
            print(f"\n⚠️  Unreadable CVs ({len(unreadable)}):")
            for c in unreadable:
                print(f"   - {c.name} ({Path(c.cv_file_url).name})")
        
        print(f"\n{'='*100}")
        print(f"✅ Test Complete!")
        print(f"{'='*100}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    engine.dispose()
    
    # Cleanup test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        print(f"🧹 Cleaned up test database")

if __name__ == "__main__":
    run_manual_ranking()
