import asyncio
import sys
import logging
from app.database import SessionLocal
from app.services.matching_service import matching_service
from app.models.job_description import JobDescription
from app.models.match import Match
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)

async def main():
    db = SessionLocal()
    job = db.query(JobDescription).first()
    if not job:
        print("No jobs found")
        return
    
    print(f"Testing with job: {job.title} (ID: {job.id}, Tenant: {job.tenant_id})")
    
    matches_before = db.query(Match).filter(Match.job_description_id == job.id).count()
    print(f"Matches before: {matches_before}")
    
    resumes_count = db.query(Resume).filter(Resume.tenant_id == job.tenant_id).count()
    print(f"Resumes count: {resumes_count}")
    
    new_matches = await matching_service.generate_matches_for_job(
        job_id=job.id,
        db=db,
        tenant_id=job.tenant_id,
        limit=50
    )
    
    print(f"Matches returned by generate_matches_for_job: {len(new_matches)}")
    matches_after = db.query(Match).filter(Match.job_description_id == job.id).count()
    print(f"Matches after: {matches_after}")

if __name__ == "__main__":
    asyncio.run(main())
