import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/cv_ranking"

async def get_ids():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # Get a job
        result = await conn.execute(text("SELECT j.id FROM ranking_jobs j JOIN candidates c ON j.id = c.job_id LIMIT 1"))
        job = result.fetchone()
        if not job:
            print("No jobs found")
            return
            
        job_id = job[0]
        print(f"JOB_ID={job_id}")
        
        # Get a candidate for this job
        result = await conn.execute(text("SELECT id, name, cv_file_url FROM candidates WHERE job_id = :job_id LIMIT 1"), {"job_id": job_id})
        candidate = result.fetchone()
        if not candidate:
            print("No candidates found for this job")
            return
            
        print(f"CANDIDATE_ID={candidate[0]}")
        print(f"CANDIDATE_NAME={candidate[1]}")
        print(f"CV_FILE_URL={candidate[2]}")

if __name__ == "__main__":
    asyncio.run(get_ids())
