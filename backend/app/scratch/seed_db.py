import sys
import os
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.job_description import JobDescription
from app.utils.security import get_password_hash

def seed_database():
    print("Initializing database tables...")
    init_db()
    
    db = SessionLocal()
    
    # Check if user already exists
    admin = db.query(User).filter(User.email == "admin@gmail.com").first()
    if admin:
        print("Database already seeded with admin user.")
        return
        
    print("Seeding database...")
    
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Local Dev Tenant")
    db.add(tenant)
    db.commit()
    
    user = User(
        id=uuid.uuid4(),
        email="admin@gmail.com",
        hashed_password=get_password_hash("Admin@123"),
        tenant_id=tenant_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Add a sample job
    job = JobDescription(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=user.id,
        title="Software Engineer",
        description="We are looking for a great Software Engineer.",
        requirements="Python, React",
        responsibilities="Build cool things",
        required_skills="Python, React",
        preferred_skills="AWS, Docker",
        location="Remote",
        experience_required=3,
        employment_type="full_time",
        status="active"
    )
    db.add(job)
    db.commit()
    
    print("Database seeded successfully! You can login with admin@gmail.com / Admin@123")
    db.close()

if __name__ == "__main__":
    seed_database()
