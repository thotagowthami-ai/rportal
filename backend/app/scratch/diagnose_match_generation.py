"""
Diagnostic script to troubleshoot match generation issues.
Run this to identify what's preventing matches from being generated.

Usage:
    python -c "import sys; sys.path.insert(0, '.'); exec(open('app/scratch/diagnose_match_generation.py').read())"
Or:
    python app/scratch/diagnose_match_generation.py
"""
import asyncio
import sys
import logging
import json
from app.database import SessionLocal
from app.services.matching_service import matching_service
from app.models.job_description import JobDescription
from app.models.match import Match
from app.models.resume import Resume
from app.config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def diagnose():
    """Run diagnostic checks on the match generation system."""
    print("\n" + "="*80)
    print("MATCH GENERATION DIAGNOSTIC REPORT")
    print("="*80 + "\n")
    
    db = SessionLocal()
    
    # Check 1: Configuration
    print("1. CONFIGURATION CHECK")
    print("-" * 80)
    print(f"   GEMINI_API_KEY: {'✓ SET' if settings.GEMINI_API_KEY else '✗ NOT SET (will use basic scoring)'}")
    print(f"   CLAUDE_API_KEY: {'✓ SET' if settings.CLAUDE_API_KEY else '✗ NOT SET'}")
    print(f"   DATABASE_URL: {settings.DATABASE_URL}")
    print(f"   CANDIDATE_PORTAL_URL: {settings.CANDIDATE_PORTAL_URL or '✗ NOT SET'}")
    print()
    
    # Check 2: Jobs and Resumes
    print("2. DATA CHECK")
    print("-" * 80)
    jobs = db.query(JobDescription).all()
    resumes = db.query(Resume).all()
    matches = db.query(Match).all()
    
    print(f"   Total Jobs: {len(jobs)}")
    print(f"   Total Resumes: {len(resumes)}")
    print(f"   Total Matches: {len(matches)}")
    print()
    
    if not jobs:
        print("   ⚠️  WARNING: No jobs found in database!")
        return
    
    if not resumes:
        print("   ⚠️  WARNING: No resumes found in database!")
        return
    
    # Check 3: Job Details
    print("3. JOB DETAILS")
    print("-" * 80)
    for i, job in enumerate(jobs[:3], 1):
        print(f"   Job #{i}: {job.title}")
        print(f"      ID: {job.id}")
        print(f"      Status: {job.status}")
        print(f"      Required Skills: {job.required_skills}")
        print(f"      Preferred Skills: {job.preferred_skills}")
        print(f"      Has Embedding: {'✓ YES' if job.embedding else '✗ NO'}")
        print()
    
    # Check 4: Resume Details
    print("4. RESUME DETAILS")
    print("-" * 80)
    for i, resume in enumerate(resumes[:3], 1):
        print(f"   Resume #{i}: {resume.candidate_name}")
        print(f"      ID: {resume.id}")
        print(f"      Email: {resume.candidate_email}")
        print(f"      Experience Years: {resume.experience_years}")
        print(f"      Skills: {resume.skills}")
        print(f"      Has Resume Text: {'✓ YES' if resume.resume_text else '✗ NO'}")
        print(f"      Has Embedding: {'✓ YES' if resume.embedding else '✗ NO'}")
        print()
    
    # Check 5: Try generating matches for first job
    if jobs and resumes:
        print("5. MATCH GENERATION TEST")
        print("-" * 80)
        job = jobs[0]
        print(f"   Testing match generation for job: {job.title}")
        print()
        
        try:
            matches = await matching_service.generate_matches_for_job(
                job_id=job.id,
                db=db,
                tenant_id=job.tenant_id,
                limit=10
            )
            print(f"   ✓ SUCCESS: Generated {len(matches)} matches")
            
            if matches:
                print()
                print("   Generated Matches:")
                for match in matches[:3]:
                    print(f"      - Score: {match.overall_score}% | Skill: {match.skill_match_score}% | Resume: {match.resume_id}")
            else:
                print("   ⚠️  WARNING: Generated 0 matches (resumes may not meet scoring threshold)")
                
        except Exception as e:
            print(f"   ✗ ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("="*80)
    print("END OF DIAGNOSTIC REPORT")
    print("="*80 + "\n")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
