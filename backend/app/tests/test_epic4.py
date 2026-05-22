"""
EPIC 4 tests: semantic matching and tenant isolation.
"""

import uuid
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/recruiting_db")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception:
            # pgvector may be unavailable in local test containers.
            conn.rollback()
        conn.execute(text("DROP FUNCTION IF EXISTS current_tenant_id();"))
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION current_tenant_id()
            RETURNS TEXT AS $$
            BEGIN
                RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '');
            EXCEPTION
                WHEN OTHERS THEN
                    RETURN NULL;
            END;
            $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
        """))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from app.services import matching_service as matching_module
    matching_module.matching_service.claude_client = None

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _register(client: TestClient) -> dict:
    payload = {
        "email": f"admin-{uuid.uuid4()}@example.com",
        "password": "StrongPass1",
        "full_name": "Admin User",
        "tenant_name": "Example Org",
        "tenant_slug": f"org-{uuid.uuid4().hex[:8]}",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    body = res.json()
    return {
        "token": body["access_token"],
        "tenant_id": body["user"]["tenant_id"],
        "user_id": body["user"]["id"],
    }


def _seed_job_and_resume(db, tenant_id: str, user_id: str) -> str:
    from app.models.job_description import JobDescription
    from app.models.resume import Resume

    embedding = [0.0] * 1023 + [1.0]

    job = JobDescription(
        tenant_id=tenant_id,
        created_by=user_id,
        title="Backend Engineer",
        description="Build APIs",
        requirements="FastAPI and SQLAlchemy",
        responsibilities="Own backend services",
        required_skills=["python", "fastapi"],
        preferred_skills=["postgresql"],
        location="Remote",
        experience_required=3,
        employment_type="full-time",
        status="active",
        embedding=embedding,
    )
    resume = Resume(
        tenant_id=tenant_id,
        uploaded_by=user_id,
        candidate_name="Jane Doe",
        candidate_email="jane@example.com",
        candidate_phone="+1-555-0102",
        file_path="uploads/resumes/jane.docx",
        file_name="jane.docx",
        file_type="docx",
        resume_text="Python FastAPI PostgreSQL",
        skills=["python", "fastapi", "postgresql"],
        experience_years=4,
        education="BS CS",
        current_role="Backend Engineer",
        embedding=embedding,
    )
    db.add(job)
    db.add(resume)
    db.commit()
    db.refresh(job)
    return str(job.id)


def test_match_generation_and_listing(client: TestClient, db_session):
    auth = _register(client)
    job_id = _seed_job_and_resume(db_session, auth["tenant_id"], auth["user_id"])
    headers = {"Authorization": f"Bearer {auth['token']}"}

    gen = client.post(f"/api/matches/generate?job_id={job_id}&limit=10", headers=headers)
    assert gen.status_code == 201
    assert gen.json()["total"] >= 1

    listed = client.get(f"/api/matches/job?job_id={job_id}&page=1&page_size=20", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_match_list_is_tenant_scoped(client: TestClient, db_session):
    auth_a = _register(client)
    auth_b = _register(client)
    job_id = _seed_job_and_resume(db_session, auth_a["tenant_id"], auth_a["user_id"])

    headers_a = {"Authorization": f"Bearer {auth_a['token']}"}
    headers_b = {"Authorization": f"Bearer {auth_b['token']}"}

    gen = client.post(f"/api/matches/generate?job_id={job_id}&limit=10", headers=headers_a)
    assert gen.status_code == 201

    listed_b = client.get(f"/api/matches/job?job_id={job_id}&page=1&page_size=20", headers=headers_b)
    assert listed_b.status_code == 200
    assert listed_b.json()["total"] == 0
