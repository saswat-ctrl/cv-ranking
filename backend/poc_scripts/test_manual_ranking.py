import asyncio
import os
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.extraction_service import extract_text
from app.services.parsing_service import parse_resume
from app.services.ranking_service import rank_candidates
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User  # Import to resolve SQLAlchemy relationships
from app.core.config import settings

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

TEST_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "test_documents")
JD_FILE = "Product Manager JD copy.pdf"
CV_FILES = [
    "Anish Sinha CV'25.pdf",
    "Saswat_Ray_PM4000.pdf",
    "Screenshot 2025-11-28 at 1.23.46 PM.jpeg",
    "example-university-student-CV-compressed.pdf"
]

async def run_manual_ranking():
    db = SessionLocal()
    try:
        print(f"--- Starting Manual Ranking Test ---")
        
        # 1. Create Job & Extract JD
        print(f"\n[1/4] Processing JD: {JD_FILE}")
        jd_path = os.path.join(TEST_DOCS_DIR, JD_FILE)
        with open(jd_path, "rb") as f:
            jd_bytes = f.read()
            
        # Save to temp file for extraction
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(jd_bytes)
            jd_temp_path = tmp.name
            
        jd_text, jd_error = await extract_text(jd_temp_path, "application/pdf")
        os.remove(jd_temp_path)
        
        if jd_error:
            print(f"❌ JD extraction failed: {jd_error}")
            return
            
        # Create dummy user
        user = User(email="test_ranking@example.com", hashed_password="hashed_password", name="Test User")
        # Check if user exists
        from sqlalchemy.future import select
        result = await db.execute(select(User).where(User.email == "test_ranking@example.com"))
        existing_user = result.scalars().first()
        if existing_user:
            user = existing_user
        else:
            db.add(user)
            await db.flush()
        
        job = Job(
            title="Test Product Manager",
            extracted_text=jd_text,
            user_id=user.id,
            file_url="manual_test"
        )
        db.add(job)
        await db.flush()  # Use flush instead of commit to get the ID
        print(f"✅ Job Created (ID: {job.id})")
        print(f"   Extracted {len(job.extracted_text)} chars")

        # 2. Process CVs
        print(f"\n[2/4] Processing {len(CV_FILES)} CVs...")
        for cv_file in CV_FILES:
            cv_path = os.path.join(TEST_DOCS_DIR, cv_file)
            print(f"   -> Processing {cv_file}...", end=" ", flush=True)
            
            with open(cv_path, "rb") as f:
                cv_bytes = f.read()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(cv_file)[1]) as tmp:
                tmp.write(cv_bytes)
                cv_temp_path = tmp.name
            
            # Extract
            mime_type = "image/jpeg" if cv_file.endswith(".jpeg") else "application/pdf"
            extracted_text, extract_error = await extract_text(cv_temp_path, mime_type)
            os.remove(cv_temp_path)
            
            # Determine readability
            is_readable = len(extracted_text.strip()) >= 100
            
            # Parse
            parse_result = {}
            if extracted_text and not extract_error:
                parse_result = await parse_resume(extracted_text)
            
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
            print(f"Done. (Readable: {candidate.is_readable})")
        
        await db.flush()  # Flush to get candidate IDs
        
        # 3. Rank Candidates
        print(f"\n[3/4] Ranking Candidates...")
        rank_result = await rank_candidates(str(job.id), db)
        
        if not rank_result["success"]:
            print(f"❌ Ranking Failed: {rank_result.get('error')}")
            return

        # 4. Display Results
        print(f"\n[4/4] 🏆 Ranking Results for '{JD_FILE}'")
        print("="*100)
        print(f"{'Rank':<5} | {'Score':<6} | {'Name':<30} | {'Semantic':<8} | {'Keyword':<8} | {'Skills':<6}")
        print("-" * 100)
        
        result = await db.execute(
            select(Candidate).filter(Candidate.job_id == job.id).order_by(Candidate.ranking_score.desc())
        )
        candidates = result.scalars().all()
        
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
                reasoning_preview = c.ranking_reasoning[:200] + "..." if len(c.ranking_reasoning) > 200 else c.ranking_reasoning
                print(f"      💡 {reasoning_preview}")
            print("-" * 100)

        unreadable = [c for c in candidates if not c.is_readable]
        if unreadable:
            print(f"\n⚠️ Unreadable CVs ({len(unreadable)}):")
            for c in unreadable:
                print(f" - {c.name} ({os.path.basename(c.cv_file_url)})")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(run_manual_ranking())
