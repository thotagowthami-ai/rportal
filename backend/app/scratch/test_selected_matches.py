import asyncio
import sys
import logging
from app.database import SessionLocal
from app.services.matching_service import matching_service
from app.models.job_description import JobDescription
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db = SessionLocal()
    job = db.query(JobDescription).first()
    if not job:
        logger.error("No jobs found")
        return
        
    resumes = db.query(Resume).filter(Resume.tenant_id == job.tenant_id).limit(2).all()
    if not resumes:
        logger.error("No resumes found")
        return
        
    resume_ids = [r.id for r in resumes]
    logger.info(f"Generating matches for Job: {job.title} (ID: {job.id}) with resumes: {resume_ids}")
    
    try:
        matches = await matching_service.generate_matches_for_job(
            job_id=job.id,
            db=db,
            tenant_id=job.tenant_id,
            limit=50,
            resume_ids=resume_ids
        )
        logger.info(f"Successfully generated {len(matches)} matches.")
        for m in matches:
            logger.info(f"Match: Resume {m.resume_id}, Score {m.overall_score}")
    except Exception as e:
        logger.exception(f"Error during match generation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
