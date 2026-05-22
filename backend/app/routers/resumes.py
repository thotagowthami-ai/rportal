from app.config import settings
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Form, Body, Request
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db, set_tenant_context
from app.api.deps import get_current_user
from app.models.resume import Resume
from app.models.user import User
from app.services.resume_parser import extract_resume_text, parse_resume_text, is_doc_conversion_available, validate_file, sanitize_filename
import uuid
import os
import json
import math
import logging
from app.services.matching_service import matching_service
from app.services.storage_service import storage_service
from app.models.job_description import JobDescription
from typing import List, Any, Dict
import httpx

# Absolute path to uploads folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def _unwrap_json_value(val):
    """Helper to extract a string value from a potential JSON item."""
    if not val:
        return ""
    if not isinstance(val, str):
        return str(val)
    
    val_s = val.strip()
    if val_s.startswith("{") and val_s.endswith("}"):
        try:
            parsed = json.loads(val_s)
            if isinstance(parsed, dict):
                for k in ["degree", "skill", "name", "title", "value"]:
                    if k in parsed:
                        return str(parsed[k])
                for v in parsed.values():
                    if isinstance(v, (str, int, float)):
                        return str(v)
            return val_s
        except Exception:
            return val_s
    return val_s


def _parse_skills(raw_skills):
    if isinstance(raw_skills, list):
        return [_unwrap_json_value(s) for s in raw_skills if s]
    if isinstance(raw_skills, str):
        try:
            parsed = json.loads(raw_skills)
            if isinstance(parsed, list):
                return [_unwrap_json_value(s) for s in parsed if s]
            return [_unwrap_json_value(raw_skills)]
        except Exception:
            if "," in raw_skills:
                return [s.strip() for s in raw_skills.split(",")]
            return [raw_skills]
    return []
    return []


def _parse_work_experience(raw_exp):
    if isinstance(raw_exp, list):
        return raw_exp
    if isinstance(raw_exp, str):
        try:
            parsed = json.loads(raw_exp)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _to_storage_skills(db: Session, skills=None):
    dialect = (db.bind.dialect.name if db.bind is not None else "").lower()
    if skills is None:
        skills = []
    if dialect == "postgresql":
        return skills
    return json.dumps(skills)


def _to_storage_work_experience(db: Session, exp=None):
    dialect = (db.bind.dialect.name if db.bind is not None else "").lower()
    if exp is None:
        exp = []
    if dialect == "postgresql":
        return exp
    return json.dumps(exp)


def _serialize_resume(resume: Resume) -> dict:
    return {
        "id": str(resume.id),
        "candidate_name": resume.candidate_name,
        "candidate_email": resume.candidate_email,
        "candidate_phone": resume.candidate_phone,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "skills": _parse_skills(resume.skills),
        "work_experience": _parse_work_experience(resume.work_experience),
        "experience_years": resume.experience_years,
        "education": resume.education,
        "current_role": resume.current_role,
        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }


def _normalize_education(raw):
    if not raw:
        return None
    if isinstance(raw, str):
        unwrapped = _unwrap_json_value(raw)
        return unwrapped if unwrapped else None
    if isinstance(raw, list):
        degrees = []
        for item in raw:
            unwrapped = _unwrap_json_value(item)
            if unwrapped:
                degrees.append(unwrapped)
        return " | ".join(degrees) if degrees else None
    return str(raw)


def _allowed_tenant_ids(current_user: User) -> list[str]:
    """
    Returns the list of tenant IDs this user is allowed to query.

    INTENTIONAL DESIGN: Portal-tenant access is granted to all authenticated
    ATS users because the candidate portal is a shared resource — candidates
    apply there without knowing which company will review them, and every
    recruiter needs to see those applications.
    To disable shared portal access, leave CANDIDATE_PORTAL_TENANT_ID unset.
    """
    user_tid = str(current_user.tenant_id)
    tenant_ids = [user_tid]

    portal_tid = str(
        settings.CANDIDATE_PORTAL_TENANT_ID or settings.RECRUITING_TENANT_ID or ""
    ).strip()

    # Append portal tenant only when configured AND distinct from the user's
    # own tenant (prevents a redundant duplicate entry for portal-tenant users).
    if portal_tid and portal_tid != user_tid:
        tenant_ids.append(portal_tid)

    return tenant_ids


# ✅ 1. List resumes
@router.get("")
def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_tenant_ids = _allowed_tenant_ids(current_user)
    query = db.query(Resume).filter(
        Resume.tenant_id.in_(allowed_tenant_ids),
        Resume.deleted_at.is_(None),
    )
    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.order_by(Resume.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        "items": [_serialize_resume(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.post("/sync")
async def sync_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually sync resumes from the Candidate Portal.
    """
    try:
        set_tenant_context(db, str(current_user.tenant_id))
        resumes = await matching_service.sync_portal_resumes(
            db=db,
            tenant_id=str(current_user.tenant_id),
            uploaded_by=str(current_user.id),
        )
        try:
            from app.routers.analytics import invalidate_analytics_cache
            invalidate_analytics_cache(str(current_user.tenant_id))
        except Exception:
            pass
        return {
            "message": f"Successfully synced {len(resumes)} resumes from Candidate Portal.",
            "count": len(resumes),
        }
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ✅ 2. Upload single resume (BEFORE /{resume_id})
@router.post("/upload", status_code=201)
async def upload_resume(
    candidate_name: str | None = Form(None),
    candidate_email: str | None = Form(None),
    candidate_phone: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    set_tenant_context(db, str(current_user.tenant_id))
    
    # Validate file size and extension centrally before reading into memory to prevent DoS memory exhaustion
    file_size = getattr(file, "size", None)
    is_valid, err_msg = validate_file(file.filename, file_size=file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    file_bytes = await file.read()
    is_valid_bytes, err_bytes_msg = validate_file(file.filename, file_bytes=file_bytes)
    if not is_valid_bytes:
        raise HTTPException(status_code=400, detail=err_bytes_msg)

    safe_filename = sanitize_filename(file.filename)
    content_type = file.content_type or ""
    file_path = storage_service.upload_bytes(
        file_bytes, safe_filename, content_type=content_type, prefix="resumes"
    )
    if not file_path:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOADS_DIR, f"{file_id}_{safe_filename}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

    resolved_name = (candidate_name or "").strip() or safe_filename
    parsed = {"candidate_email": "", "candidate_phone": "", "skills": [], "experience_years": 0, "education": "", "current_role": ""}
    resume_text = None

    try:
        resume_text = extract_resume_text(file_bytes, file.filename, content_type)
        parsed = parse_resume_text(resume_text or "")
        logger.info(f"Resume parsed successfully: {safe_filename}")
    except Exception as e:
        logger.error(f"Error parsing resume '{safe_filename}': parse failed")

    file_ext = os.path.splitext(safe_filename)[1].lower().lstrip(".")
    resume = Resume(
        tenant_id=str(current_user.tenant_id),
        uploaded_by=str(current_user.id),
        candidate_name=resolved_name,
        candidate_email=(candidate_email or parsed.get("candidate_email") or None),
        candidate_phone=(candidate_phone or parsed.get("candidate_phone") or None),
        file_path=file_path,
        file_name=safe_filename,
        file_type=file_ext,
        resume_text=resume_text,
        skills=_to_storage_skills(db, parsed.get("skills", [])),
        work_experience=_to_storage_work_experience(db, parsed.get("work_experience", [])),
        experience_years=(parsed.get("experience_years") or None),
        education=_normalize_education(parsed.get("education")),
        current_role=(parsed.get("current_role") or None),
    )
    db.add(resume)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")
    db.refresh(resume)
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass
    return _serialize_resume(resume)


# ✅ 3. Upload multiple resumes (BEFORE /{resume_id})
@router.post("/upload-multiple", status_code=201)
async def upload_multiple_resumes(
    candidate_name: str | None = Form(None),
    candidate_email: str | None = Form(None),
    candidate_phone: str | None = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    set_tenant_context(db, str(current_user.tenant_id))
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
    created_resumes = []

    for file in files:
        # Validate file size and extension centrally before reading into memory to prevent DoS memory exhaustion
        file_size = getattr(file, "size", None)
        is_valid, err_msg = validate_file(file.filename, file_size=file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)

        file_bytes = await file.read()
        is_valid_bytes, err_bytes_msg = validate_file(file.filename, file_bytes=file_bytes)
        if not is_valid_bytes:
            continue

        safe_filename = sanitize_filename(file.filename)
        content_type = file.content_type or ""
        file_path = storage_service.upload_bytes(
            file_bytes, safe_filename, content_type=content_type, prefix="resumes"
        )
        if not file_path:
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            file_id = str(uuid.uuid4())
            file_path = os.path.join(UPLOADS_DIR, f"{file_id}_{safe_filename}")
            with open(file_path, "wb") as buffer:
                buffer.write(file_bytes)
        
        resolved_name = (candidate_name or "").strip() or safe_filename
        parsed = {"candidate_email": "", "candidate_phone": "", "skills": [], "experience_years": 0, "education": "", "current_role": ""}
        resume_text = None

        try:
            resume_text = extract_resume_text(file_bytes, file.filename, content_type)
            parsed = parse_resume_text(resume_text or "")
            logger.info(f"Resume parsed successfully: {safe_filename}")
        except Exception as e:
            logger.error(f"Error parsing resume '{safe_filename}': parse failed")

        file_ext = os.path.splitext(safe_filename)[1].lower().lstrip(".")
        resume = Resume(
            tenant_id=str(current_user.tenant_id),
            uploaded_by=str(current_user.id),
            candidate_name=resolved_name,
            candidate_email=(candidate_email or parsed.get("candidate_email") or None),
            candidate_phone=(candidate_phone or parsed.get("candidate_phone") or None),
            file_path=file_path,
            file_name=safe_filename,
            file_type=file_ext,
            resume_text=resume_text,
            skills=_to_storage_skills(db, parsed.get("skills", [])),
            work_experience=_to_storage_work_experience(db, parsed.get("work_experience", [])),
            experience_years=(parsed.get("experience_years") or None),
            education=_normalize_education(parsed.get("education")),
            current_role=(parsed.get("current_role") or None),
        )
        db.add(resume)
        created_resumes.append(resume)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save resumes: {str(e)}")

    for resume in created_resumes:
        db.refresh(resume)
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass

    return [_serialize_resume(r) for r in created_resumes]


# ✅ 3b. Public Apply for Job
@router.post("/public/apply", status_code=201)
async def public_apply_job(
    job_id: str = Form(...),
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    candidate_phone: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Public apply endpoint for candidates without needing a login."""
    # 1. Fetch Job to get context
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.status == "active",
        JobDescription.deleted_at.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or no longer active")

    set_tenant_context(db, str(job.tenant_id))

    # 2. Extract & Save Resume
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Validate file size and extension centrally before reading into memory to prevent DoS memory exhaustion
    file_size = getattr(file, "size", None)
    is_valid, err_msg = validate_file(file.filename, file_size=file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    file_bytes = await file.read()
    is_valid_bytes, err_bytes_msg = validate_file(file.filename, file_bytes=file_bytes)
    if not is_valid_bytes:
        raise HTTPException(status_code=400, detail=err_bytes_msg)
    safe_filename = sanitize_filename(file.filename)
    file_path = storage_service.upload_bytes(
        file_bytes, safe_filename, content_type=file.content_type or "", prefix="resumes"
    )
    if not file_path:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOADS_DIR, f"{file_id}_{safe_filename}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

    # 3. Parse Resume
    resume_text = None
    parsed = {}
    try:
        resume_text = extract_resume_text(file_bytes, file.filename, file.content_type or "")
        parsed = parse_resume_text(resume_text or "")
    except Exception as e:
        logger.error(f"Error parsing public resume {file.filename}: {e}")

    # 4. Create Resume Record
    job_creator = getattr(job, "created_by", None) or getattr(job, "created_by_id", None)
    file_ext = os.path.splitext(safe_filename)[1].lower().lstrip(".")
    resume = Resume(
        tenant_id=str(job.tenant_id),
        uploaded_by=str(job_creator) if job_creator else None,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone or parsed.get("candidate_phone") or None,
        file_path=file_path,
        file_name=safe_filename,
        file_type=file_ext,
        resume_text=resume_text,
        skills=_to_storage_skills(db, parsed.get("skills", [])),
        work_experience=_to_storage_work_experience(db, parsed.get("work_experience", [])),
        experience_years=(parsed.get("experience_years") or None),
        education=_normalize_education(parsed.get("education")),
        current_role=(parsed.get("current_role") or None),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(job.tenant_id))
    except Exception:
        pass

    # 5. Trigger Matching
    try:
        await matching_service.generate_matches_for_job(
            job_id=str(job.id),
            db=db,
            tenant_id=str(job.tenant_id),
            resume_ids=[str(resume.id)]
        )
    except Exception as e:
        logger.warning(f"Auto-match failed for public apply: {e}")

    return {"message": "Application submitted successfully", "resume_id": str(resume.id)}


# ✅ 5. Re-analyze
@router.post("/{resume_id}/re-analyze")
def re_analyze_resume(
    resume_id: str,
    payload: dict | None = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_id = (resume_id or "").strip()
    try:
        resume_id = str(uuid.UUID(resume_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid resume_id")

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.tenant_id.in_(_allowed_tenant_ids(current_user)),
            Resume.deleted_at.is_(None),
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = str(resume.resume_text) if resume.resume_text else ""
    parsed = {
        "candidate_email": "",
        "candidate_phone": "",
        "skills": [],
        "experience_years": 0,
        "education": "",
        "current_role": "",
    }
    if resume_text:
        try:
            parsed = parse_resume_text(resume_text)
        except Exception as e:
            logger.error(f"Error re-analyzing resume: {e}")

    resume.skills = _to_storage_skills(db, parsed.get("skills", []))
    resume.work_experience = _to_storage_work_experience(db, parsed.get("work_experience", []))
    resume.experience_years = parsed.get("experience_years") or resume.experience_years
    resume.education = _normalize_education(parsed.get("education")) or resume.education

    resume.current_role = parsed.get("current_role") or resume.current_role
    resume.candidate_email = parsed.get("candidate_email") or resume.candidate_email
    resume.candidate_phone = parsed.get("candidate_phone") or resume.candidate_phone

    db.commit()
    db.refresh(resume)
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(resume.tenant_id))
    except Exception:
        pass
    return _serialize_resume(resume)


# ✅ New validation dependency for short-lived one-time download tokens
def get_download_user(
    token: str | None = Query(None),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    from app.services.cache_service import cache_service
    import json
    
    # 1. Check if standard Authorization header is present
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.startswith("Bearer "):
        from app.api.deps import get_current_user
        token_str = auth_header.split(" ", 1)[1]
        return get_current_user(token=token_str, db=db)
        
    # 2. Check for short-lived one-time download token in query parameter
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials are required."
        )
        
    payload_str = cache_service.get(key=f"download_token:{token}")
    if not payload_str:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired download token"
        )
        
    # Enforce strict one-time use immediately
    cache_service.delete(key=f"download_token:{token}")
    
    try:
        payload = json.loads(payload_str)
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid token structure")

    set_tenant_context(db, uuid.UUID(tenant_id))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # Attach token payload to request state so download_resume can verify resume_id binding
    if request:
        request.state.download_token_payload = payload
    return user


# ✅ New POST endpoint to request a short-lived one-time download token
@router.post("/{resume_id}/download-token")
def generate_download_token(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_id = (resume_id or "").strip()
    try:
        resume_uuid = str(uuid.UUID(resume_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid resume_id")
        
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_uuid,
            Resume.tenant_id.in_(_allowed_tenant_ids(current_user)),
            Resume.deleted_at.is_(None),
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    import secrets
    import json
    from app.services.cache_service import cache_service
    
    download_token = secrets.token_urlsafe(32)
    payload = {
        "user_id": str(current_user.id),
        "tenant_id": str(current_user.tenant_id),
        "resume_id": str(resume.id)
    }
    # 15-second TTL is extremely secure and robust for browser transitions
    # Pass dict directly — cache_service.set() handles json.dumps internally
    cache_service.set(key=f"download_token:{download_token}", value=payload, ttl=15)
    return {"download_token": download_token}


# ✅ 7. Download
@router.get("/{resume_id}/download")
def download_resume(
    resume_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_download_user),
):
    # If this request used a one-time download token, verify the token was
    # issued specifically for this resume to prevent replay across resumes.
    token_payload = getattr(getattr(request, "state", None), "download_token_payload", None)
    if token_payload is not None:
        token_resume_id = token_payload.get("resume_id")
        if not token_resume_id or token_resume_id != resume_id:
            raise HTTPException(status_code=403, detail="Download token is not valid for this resume")

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.tenant_id.in_(_allowed_tenant_ids(current_user)),
            Resume.deleted_at.is_(None),
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    file_path = resume.file_path if resume.file_path else None
    
    # 1. Handle Candidate Portal resumes (Proxy)
    if file_path and file_path.startswith("candidate_portal/"):
        candidate_id = file_path.replace("candidate_portal/", "")
        portal_base = getattr(settings, "CANDIDATE_PORTAL_URL", "https://candidateportal-production.up.railway.app/api")
        download_url = f"{portal_base}/resumes/{candidate_id}/download"
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                portal_resp = client.get(download_url)
                if portal_resp.status_code == 200:
                    content = portal_resp.content
                    media_type = portal_resp.headers.get("content-type", "application/pdf")
                    filename = resume.file_name or f"{candidate_id}.pdf"
                    return StreamingResponse(
                        iter([content]),
                        media_type=media_type,
                        # CHANGED TO INLINE
                        headers={"Content-Disposition": f'inline; filename="{filename}"'},
                    )
        except Exception as e:
            logger.warning(f"Portal proxy download failed for {candidate_id}: {e}")
        raise HTTPException(status_code=404, detail="Could not retrieve resume from Candidate Portal.")

    # 2. Try R2 storage or cloud URLs
    if file_path:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            refreshed_url = storage_service.get_url_for_key(file_path)
            if refreshed_url:
                return RedirectResponse(url=refreshed_url)
            return RedirectResponse(url=file_path)
            
        obj = storage_service.get_object_stream(file_path)
        if obj:
            body, _length = obj
            ext = (resume.file_type or "").lower()
            media_type_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "doc": "application/msword",
            }
            media_type = media_type_map.get(ext, "application/octet-stream")
            return StreamingResponse(
                body.iter_chunks(chunk_size=1024 * 1024),
                media_type=media_type,
                # CHANGED TO INLINE
                headers={"Content-Disposition": f'inline; filename="{resume.file_name}"'},
            )

    # 3. Fallback: Search local uploads folder
    local_path = file_path
    if not local_path or not os.path.exists(local_path):
        target_name = resume.file_name or ""
        if os.path.exists(UPLOADS_DIR):
            for f in os.listdir(UPLOADS_DIR):
                if f == target_name or f.endswith(f"_{target_name}") or f.startswith(str(resume_id)):
                    local_path = os.path.join(UPLOADS_DIR, f)
                    break

    if local_path:
        real_local = os.path.realpath(local_path)
        real_uploads = os.path.realpath(UPLOADS_DIR)
        prefix = real_uploads if real_uploads.endswith(os.sep) else real_uploads + os.sep
        if not real_local.startswith(prefix):
            raise HTTPException(status_code=400, detail="Invalid path or path traversal detected")

    if local_path and os.path.exists(local_path):
        if not os.access(local_path, os.R_OK):
            raise HTTPException(status_code=500, detail="File is not readable")
            
        ext = (resume.file_type or "").lower()
        media_type_map = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "doc": "application/msword"}
        media_type = media_type_map.get(ext, "application/octet-stream")
        
        # CHANGED TO INLINE
        return FileResponse(
            path=local_path, 
            media_type=media_type,
            headers={"Content-Disposition": f'inline; filename="{resume.file_name}"'}
        )

    raise HTTPException(status_code=404, detail=f"Resume file '{resume.file_name}' not found. Please re-upload.")


# ✅ 6. Delete
@router.delete("/{resume_id}")
def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.tenant_id.in_(_allowed_tenant_ids(current_user)),
            Resume.deleted_at.is_(None),
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    from datetime import datetime

    resume.deleted_at = datetime.utcnow()
    db.commit()
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(resume.tenant_id))
    except Exception:
        pass
    return {"message": "Resume deleted successfully"}


# ✅ 4. Get single resume (AFTER upload routes)
@router.get("/{resume_id}")
def get_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.tenant_id.in_(_allowed_tenant_ids(current_user)),
            Resume.deleted_at.is_(None),
        )
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return _serialize_resume(resume)
