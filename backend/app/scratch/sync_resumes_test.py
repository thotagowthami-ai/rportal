import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.matching_service import matching_service
from app.config import settings
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)

async def test_sync():
    engine = create_engine(settings.async_database_url.replace("+asyncpg", "").replace("+aiosqlite", ""))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Get a tenant_id
    user = db.query(User).first()
    if not user:
        print("No users found in database.")
        return
        
    print(f"Syncing for tenant_id: {user.tenant_id}")
    resumes = await matching_service.sync_portal_resumes(db, str(user.tenant_id), str(user.id))
    print(f"Synced {len(resumes)} resumes.")
    for r in resumes:
        print(f" - {r.candidate_name} ({r.candidate_email})")

if __name__ == "__main__":
    asyncio.run(test_sync())
