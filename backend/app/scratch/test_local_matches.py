import asyncio
import sys
from app.database import SessionLocal
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.services.matching_service import matching_service

async def run():
    db = SessionLocal()
    job = db.query(JobDescription).first()
    if not job:
        print("No job found")
        return
    resumes = db.query(Resume).all()
    print("Job:", job.title, "Resumes:", len(resumes))
    if not resumes:
        return
    try:
        await matching_service.generate_matches_for_job(
            str(job.id), 
            db, 
            str(job.tenant_id), 
            50, 
            [str(r.id) for r in resumes]
        )
        print('Done generating')
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    asyncio.run(run())
