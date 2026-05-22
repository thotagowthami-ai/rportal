"""
EPIC 5 tests: analytics dashboard and tenant isolation.
"""

import uuid
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL environment variable is required")


def _validate_test_db_url(url: str) -> None:
    from sqlalchemy.engine.url import make_url
    try:
        parsed_url = make_url(url)
    except Exception:
        raise RuntimeError(
            f"Unsafe database URL detected: '{url}'. "
            "TEST_DATABASE_URL must point to an isolated test database containing 'test' keyword."
        )
    db_name = parsed_url.database or ""
    host = parsed_url.host or ""
    is_sqlite = url.lower().startswith("sqlite")
    
    allow_destructive = os.environ.get("TEST_ALLOW_DESTRUCTIVE", "").lower() == "true"
    is_test_db = (
        "test" in db_name.lower() or
        is_sqlite or
        allow_destructive
    )
    if not is_test_db:
        raise RuntimeError(
            f"Unsafe database URL detected: '{url}'. "
            "TEST_DATABASE_URL must point to an isolated test database containing 'test' keyword."
        )


_validate_test_db_url(TEST_DATABASE_URL)
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
        _validate_test_db_url(TEST_DATABASE_URL)
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

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


def _seed_job_resume_match(db, tenant_id: str, user_id: str) -> str:
    from app.models.job_description import JobDescription
    from app.models.match import Match
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
    db.flush()

    match = Match(
        tenant_id=tenant_id,
        job_description_id=job.id,
        resume_id=resume.id,
        overall_score=88.0,
        recruiter_status="new",
    )
    db.add(match)
    db.commit()
    return str(job.id)


def test_dashboard_empty_state(client: TestClient):
    auth = _register(client)
    headers = {"Authorization": f"Bearer {auth['token']}"}
    res = client.get("/api/analytics/dashboard", headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["jobs_count"] == 0
    assert body["resumes_count"] == 0
    assert body["matches_count"] == 0
    assert body["recent_jobs"] == []


def test_dashboard_with_data(client: TestClient, db_session):
    auth = _register(client)
    _seed_job_resume_match(db_session, auth["tenant_id"], auth["user_id"])
    headers = {"Authorization": f"Bearer {auth['token']}"}
    res = client.get("/api/analytics/dashboard", headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["jobs_count"] >= 1
    assert body["resumes_count"] >= 1
    assert body["matches_count"] >= 1
    assert len(body["recent_jobs"]) >= 1


def test_dashboard_tenant_isolation(client: TestClient, db_session):
    auth_a = _register(client)
    auth_b = _register(client)
    _seed_job_resume_match(db_session, auth_a["tenant_id"], auth_a["user_id"])

    headers_b = {"Authorization": f"Bearer {auth_b['token']}"}
    res_b = client.get("/api/analytics/dashboard", headers=headers_b)

    assert res_b.status_code == 200
    body_b = res_b.json()
    assert body_b["jobs_count"] == 0
    assert body_b["resumes_count"] == 0
    assert body_b["matches_count"] == 0
