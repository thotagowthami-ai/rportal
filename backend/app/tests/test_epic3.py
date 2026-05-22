"""
EPIC 3 Automated Tests

Covers:
- Job Descriptions CRUD
- Resume upload and listing
"""

import io
import os
import zipfile
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Test database URL (use separate test database)
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL environment variable is required")

def _validate_test_db_url(url: str):
    if not url:
        raise RuntimeError(
            f"Unsafe database URL detected: '{url}'. "
            "TEST_DATABASE_URL must point to an isolated test database containing 'test' keyword."
        )
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
    username = parsed_url.username or ""
    is_sqlite = url.lower().startswith("sqlite")
    is_test_db = (
        "test" in db_name.lower() or
        "test" in host.lower() or
        "localhost" in host.lower() or
        "127.0.0.1" in host.lower() or
        is_sqlite
    )
    if not is_test_db:
        raise RuntimeError(
            f"Unsafe database URL detected: '{url}'. "
            "TEST_DATABASE_URL must point to an isolated test database containing 'test' keyword."
        )

# Fail fast at engine creation time
_validate_test_db_url(TEST_DATABASE_URL)
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    # Enforce check before any database extends/modifications
    _validate_test_db_url(TEST_DATABASE_URL)
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
def client(db_session, monkeypatch):
    """Create test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Avoid external embedding calls
    async def _fake_embedding(*args, **kwargs):
        return None

    from app.services import embedding_service as embedding_module
    monkeypatch.setattr(embedding_module.embedding_service, "generate_embedding", _fake_embedding)

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _signup_and_get_token(client: TestClient) -> str:
    response = client.post("/api/auth/register", json={
        "email": f"admin-{uuid.uuid4()}@example.com",
        "password": "StrongPass1",
        "full_name": "Admin User",
        "tenant_name": "Example Org",
        "tenant_slug": f"org-{uuid.uuid4().hex[:8]}",
    })
    assert response.status_code == 201
    data = response.json()
    return data["access_token"]


def _make_docx_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
""")
        zf.writestr("word/document.xml", f"""
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>
""")
    return buf.getvalue()


def test_job_descriptions_crud(client: TestClient):
    token = _signup_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_payload = {
        "title": "Senior Backend Engineer",
        "description": "Build scalable APIs and services for the recruiting platform with reliability, security, and performance.",
        "requirements": "5+ years of Python and FastAPI experience, strong database design, and production API security knowledge.",
        "responsibilities": "Own core backend services, review code, and improve system reliability.",
        "required_skills": ["python", "fastapi", "postgresql", "sqlalchemy"],
        "preferred_skills": ["redis", "celery"],
        "location": "Remote",
        "salary_min": 120000,
        "salary_max": 160000,
        "experience_required": 5,
        "employment_type": "full-time",
        "status": "draft"
    }

    create_resp = client.post("/api/jobs", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    list_resp = client.get("/api/jobs?page=1&page_size=20", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    get_resp = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id

    update_resp = client.patch(f"/api/jobs/{job_id}", json={"status": "active"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "active"

    delete_resp = client.delete(f"/api/jobs/{job_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_after_delete = client.get("/api/jobs?page=1&page_size=20", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["total"] == 0


def test_resume_upload_and_list(client: TestClient):
    token = _signup_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    docx_bytes = _make_docx_bytes("John Doe\nSkills: Python, FastAPI, PostgreSQL\n5 years experience")
    files = {
        "file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    data = {
        "candidate_name": "John Doe",
        "candidate_email": "john@example.com",
        "candidate_phone": "+1-555-0101"
    }

    upload_resp = client.post("/api/resumes/upload", headers=headers, files=files, data=data)
    assert upload_resp.status_code == 201
    resume_id = upload_resp.json()["id"]

    list_resp = client.get("/api/resumes?page=1&page_size=20", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    get_resp = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == resume_id
