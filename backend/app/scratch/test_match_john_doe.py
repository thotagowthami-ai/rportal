import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, set_tenant_context
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.match import Match
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user import User
from app.services.matching_service import matching_service

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def run_test():
    db = TestingSessionLocal()
    
    tenant_id_str = str(uuid.uuid4())
    
    # Create tenant
    tenant = Tenant(id=tenant_id_str, name="Test Tenant", slug="test-tenant")
    db.add(tenant)
    db.commit()
    
    set_tenant_context(db, tenant_id_str)
    
    # Create User
    user = User(
        id=str(uuid.uuid4()),
        email='admin@gmail.com',
        hashed_password='...',
        full_name='Admin',
        tenant_id=tenant_id_str,
        role='admin',
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Create Job
    job = JobDescription(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id_str,
        created_by=user.id,
        title="Software Engineer",
        description="Test Job",
        status="active",
        created_at=datetime.utcnow() - timedelta(days=2),
        updated_at=datetime.utcnow()
    )
    db.add(job)
    
    # Create Old Resumes (50 of them)
    old_resumes = []
    for i in range(50):
        r = Resume(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id_str,
            uploaded_by="test",
            candidate_name=f"Old Candidate {i}",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(r)
        old_resumes.append(r)
        
        # They all have existing outdated matches
        m = Match(
            tenant_id=tenant_id_str,
            job_description_id=job.id,
            resume_id=r.id,
            overall_score=50.0,
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(m)
    
    # Create New Resume (JOHN DOE)
    new_resume = Resume(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id_str,
        uploaded_by="test",
        candidate_name="JOHN DOE",
        created_at=datetime.utcnow()
    )
    db.add(new_resume)
    
    db.commit()
    
    print("Database seeded with 1 Job, 50 old resumes (with old matches), and 1 new resume (JOHN DOE).")
    
    try:
        # Trigger generate_matches_for_job
        matches = await matching_service.generate_matches_for_job(
            job_id=str(job.id),
            db=db,
            tenant_id=str(tenant_id),
            limit=50
        )
        
        print(f"Generated {len(matches)} matches.")
        
        # Check if JOHN DOE is in the returned matches
        john_doe_matched = any(m.resume_id == new_resume.id for m in matches)
        print(f"JOHN DOE matched: {john_doe_matched}")
        
        if john_doe_matched:
            # Let's find its position
            for idx, m in enumerate(matches):
                if m.resume_id == new_resume.id:
                    print(f"JOHN DOE match found at index {idx} in returned matches.")
                    break
        else:
            print("ERROR: JOHN DOE was NOT processed!")
            
    except Exception as e:
        print(f"Exception during matching: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
