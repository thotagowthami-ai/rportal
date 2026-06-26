import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, set_tenant_context
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.match import Match
from app.models.tenant import Tenant
from app.models.user import User
from app.services.matching_service import matching_service

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def run_test():
    db = TestingSessionLocal()
    tenant_id_str = str(uuid.uuid4())
    tenant = Tenant(id=tenant_id_str, name="Test Tenant", slug="test-tenant")
    db.add(tenant)
    db.commit()
    set_tenant_context(db, tenant_id_str)
    
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
    db.commit()

    r = Resume(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id_str,
        uploaded_by=user.id,
        candidate_name="Test Candidate",
        file_path="test.pdf",
        file_name="test.pdf",
        created_at=datetime.utcnow()
    )
    db.add(r)
    db.commit()

    print(f"Resumes count: {db.query(Resume).count()}")

    try:
        matches = await matching_service.generate_matches_for_job(
            job_id=str(job.id),
            db=db,
            tenant_id=tenant_id_str,
            limit=50
        )
        print(f"Matches returned: {len(matches)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
