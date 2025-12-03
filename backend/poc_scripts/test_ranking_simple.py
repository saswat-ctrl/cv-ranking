"""
Simple manual ranking test using sync database session.
This bypasses the async complexity for quick testing.
"""
import asyncio
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import tempfile

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.extraction_service import extract_text
from app.services.parsing_service import parse_resume
from app.services.embedding_service import generate_embedding, generate_embeddings_batch, deserialize_embedding
from app.services.scoring_service import (
    calculate_semantic_similarity,
    calculate_keyword_similarity_batch,
    extract_matching_skills,
    calculate_final_score,
    generate_reasoning
)
from app.services.skills_service import load_skills_database
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User
from app.core.config import settings

# Create sync engine
SYNC_DATABASE_URI = settings.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "")
engine = create_engine(SYNC_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_DOCS_DIR = "/app/test_documents"
JD_FILE = "Product Manager JD copy.pdf"
CV_FILES = [
    "Anish Sinha CV'25.pdf",
    "Saswat_Ray_PM4000.pdf",
    "Screenshot 2025-11-28 at 1.23.46 PM.jpeg",
    "example-university-student-CV-compressed.pdf"
]

async def main():
    db = SessionLocal()
    try:
        print("="*100)
        print("🎯 CV RANKING TEST - Product Manager Position")
        print("="*100)
        
        # 1. Extract JD
        print(f"\n📄 Processing Job Description: {JD_FILE}")
        jd_path = os.path.join(TEST_DOCS_DIR, JD_FILE)
        with open(jd_path, "rb") as f:
            jd_bytes = f.read()
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(jd_bytes)
            jd_temp_path = tmp.name
            
        jd_text, jd_error = await extract_text(jd_temp_path, "application/pdf")
        os.remove(jd_temp_path)
        
        if jd_error:
            print(f"❌ JD extraction failed: {jd_error}")
            return
            
        print(f"✅ Extracted {len(jd_text)} characters from JD")
        
        # 2. Generate JD embedding
        print(f"\n🧠 Generating JD embedding...")
        jd_embedding_bytes, jd_emb_error = generate_embedding(jd_text)
        if jd_emb_error:
            print(f"❌ JD embedding failed: {jd_emb_error}")
            return
        print(f"✅ JD embedding generated")
        
        # 3. Process CVs
        print(f"\n📋 Processing {len(CV_FILES)} Candidate CVs...")
        print("-"*100)
        
        candidates_data = []
        for idx, cv_file in enumerate(CV_FILES, 1):
            cv_path = os.path.join(TEST_DOCS_DIR, cv_file)
            print(f"\n[{idx}/{len(CV_FILES)}] {cv_file}")
            
            with open(cv_path, "rb") as f:
                cv_bytes = f.read()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(cv_file)[1]) as tmp:
                tmp.write(cv_bytes)
                cv_temp_path = tmp.name
            
            # Extract
            mime_type = "image/jpeg" if cv_file.endswith(".jpeg") else "application/pdf"
            extracted_text, extract_error = await extract_text(cv_temp_path, mime_type)
            os.remove(cv_temp_path)
            
            is_readable = len(extracted_text.strip()) >= 100
            
            # Parse
            parse_result = {}
            if extracted_text and not extract_error:
                parse_result = await parse_resume(extracted_text)
            
            name = parse_result.get("name") or f"Candidate {idx}"
            email = parse_result.get("email") or f"candidate{idx}@example.com"
            skills = parse_result.get("skills", [])
            
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Skills: {len(skills)} found")
            print(f"   Readable: {'✅' if is_readable else '❌'}")
            
            candidates_data.append({
                "name": name,
                "email": email,
                "text": extracted_text,
                "skills": skills,
                "is_readable": is_readable,
                "file": cv_file
            })
        
        # 4. Rank candidates
        print(f"\n\n🏆 RANKING CANDIDATES...")
        print("="*100)
        
        readable_candidates = [c for c in candidates_data if c["is_readable"]]
        if len(readable_candidates) < 2:
            print(f"❌ Need at least 2 readable candidates (found {len(readable_candidates)})")
            return
        
        # Generate embeddings for readable candidates
        cv_texts = [c["text"] for c in readable_candidates]
        cv_embeddings = generate_embeddings_batch(cv_texts)
        
        # Deserialize JD embedding
        jd_embedding_np = deserialize_embedding(jd_embedding_bytes)
        
        # Calculate keyword scores (batch)
        keyword_scores = calculate_keyword_similarity_batch(jd_text, cv_texts)
        
        # Calculate semantic and skill scores for each candidate
        ranked = []
        for i, candidate in enumerate(readable_candidates):
            # Deserialize CV embedding
            cv_embedding_np = deserialize_embedding(cv_embeddings[i])
            
            # Semantic similarity
            semantic_score = calculate_semantic_similarity(jd_embedding_np, cv_embedding_np)
            
            # Keyword score (already calculated in batch)
            keyword_score = keyword_scores[i]
            
            # Skill matching
            matching_skills = extract_matching_skills(jd_text, candidate["skills"])
            all_jd_skills = load_skills_database()
            jd_mentioned_skills = extract_matching_skills(jd_text, all_jd_skills)
            skill_match_ratio = len(matching_skills) / max(len(jd_mentioned_skills), 1)
            
            # Final score
            final_score = calculate_final_score(semantic_score, keyword_score, skill_match_ratio)
            
            # Reasoning
            reasoning_data = generate_reasoning(semantic_score, keyword_score, matching_skills)
            
            ranked.append({
                **candidate,
                "final_score": final_score,
                "semantic_score": semantic_score * 100,
                "keyword_score": keyword_score * 100,
                "skill_score": skill_match_ratio * 100,
                "matching_skills": matching_skills,
                "reasoning": reasoning_data["explanation"]
            })
        
        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 5. Display Results
        print(f"\n{'Rank':<6} {'Score':<8} {'Name':<35} {'Semantic':<10} {'Keyword':<10} {'Skills':<8}")
        print("-"*100)
        
        for idx, c in enumerate(ranked, 1):
            print(f"#{idx:<5} {c['final_score']:<8.1f} {c['name'][:34]:<35} {c['semantic_score']:<10.1f} {c['keyword_score']:<10.1f} {len(c['skills']):<8}")
            print(f"       💡 {c['reasoning']}")
            print("-"*100)
        
        # Show unreadable
        unreadable = [c for c in candidates_data if not c["is_readable"]]
        if unreadable:
            print(f"\n⚠️  UNREADABLE CVs ({len(unreadable)}):")
            for c in unreadable:
                print(f"   - {c['name']} ({c['file']})")
        
        print(f"\n✅ Ranking Complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
