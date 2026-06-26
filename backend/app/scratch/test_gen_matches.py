import asyncio
import sys
import logging
from app.database import SessionLocal
from app.services.matching_service import matching_service
from app.models.job_description import JobDescription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    db = SessionLocal()
    job = db.query(JobDescription).first()
    if not job:
        logger.error("No jobs found")
        return
        
    logger.info(f"Generating matches for Job: {job.title} (ID: {job.id})")
    try:
        matches = await matching_service.generate_matches_for_job(
            job_id=job.id,
            db=db,
            tenant_id=job.tenant_id,
            limit=50
        )
        logger.info(f"Successfully generated {len(matches)} matches.")
    except Exception as e:
        logger.exception(f"Error during match generation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
