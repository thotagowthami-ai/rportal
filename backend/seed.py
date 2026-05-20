import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db, engine
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.job_description import JobDescription, JobStatus
import json

def seed():
    print("Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        # 1. Create Tenant
        tenant_email = "admin@aura.com"
        existing_user = db.query(User).filter(User.email == tenant_email).first()
        if existing_user:
            print(f"User {tenant_email} already exists. Skipping seed.")
            return

        print("Creating default tenant...")
        tenant = Tenant(
            name="Aura Demo Corp",
            slug="aura-demo",
            is_active=True
        )
        db.add(tenant)
        db.flush()
        
        # 2. Create Admin User
        print("Creating admin user...")
        admin = User(
            email=tenant_email,
            full_name="Aura Admin",
            hashed_password=User.hash_password("password123"),
            tenant_id=tenant.id,
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.flush()
        
        # 3. Create Sample Jobs
        print("Creating sample jobs...")
        jobs = [
            {
                "title": "Senior Frontend Engineer",
                "description": "We are looking for a React expert to help us build the next generation of recruitment tools.",
                "requirements": "5+ years of experience with React, TypeScript, and modern CSS frameworks.",
                "required_skills": json.dumps(["React", "TypeScript", "Tailwind CSS", "Next.js"]),
                "location": "Remote",
                "salary_range": "$140k - $180k",
                "status": JobStatus.ACTIVE.value
            },
            {
                "title": "Backend Python Developer",
                "description": "Help us scale our FastAPI backend and matching engine.",
                "requirements": "Strong experience with Python 3.9+, SQLAlchemy, and Postgres.",
                "required_skills": json.dumps(["Python", "FastAPI", "PostgreSQL", "Redis"]),
                "location": "San Francisco, CA",
                "salary_range": "$150k - $190k",
                "status": JobStatus.ACTIVE.value
            }
        ]
        
        for job_data in jobs:
            job = JobDescription(
                **job_data,
                tenant_id=tenant.id,
                created_by=admin.id
            )
            db.add(job)
            
        db.commit()
        print("Seeding completed successfully!")
        print(f"Login: {tenant_email} / password123")
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Seeding failed: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
