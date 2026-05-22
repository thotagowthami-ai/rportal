from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.job_description import JobDescription
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionFromTextCreate,
    JobDescriptionUpdate,
    JobDescriptionResponse,
    JobDescriptionList
)
from app.services.embedding_service import embedding_service
from app.services.matching_service import matching_service
import logging
import math
import json
import re



logger = logging.getLogger(__name__)


router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])


@router.get("/public/list", response_model=JobDescriptionList)
async def list_jobs_public(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """List only active job descriptions for candidates"""
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than or equal to 1")
    if page_size > 500:
        raise HTTPException(status_code=400, detail="Page size cannot exceed 500")

    query = db.query(JobDescription).filter(
        JobDescription.status == "active",
        JobDescription.deleted_at.is_(None)
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    jobs = query.order_by(JobDescription.created_at.desc()).offset(offset).limit(page_size).all()
    
    items = [
        JobDescriptionResponse(
            id=str(job.id),
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            required_skills=_to_list(job.required_skills),
            preferred_skills=_to_list(job.preferred_skills),
            location=job.location,
            salary_min=_parse_salary(job.salary_range)[0],
            salary_max=_parse_salary(job.salary_range)[1],
            experience_required=job.experience_required,
            education_required=job.education_required,
            employment_type=job.employment_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        for job in jobs
    ]
    
    return JobDescriptionList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/public/{job_id}", response_model=JobDescriptionResponse)
async def get_job_public(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific active job for public view"""
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.status == "active",
        JobDescription.deleted_at.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or is no longer active")
    
    return JobDescriptionResponse(
        id=str(job.id),
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        responsibilities=job.responsibilities,
        required_skills=_to_list(job.required_skills),
        preferred_skills=_to_list(job.preferred_skills),
        location=job.location,
        salary_min=_parse_salary(job.salary_range)[0],
        salary_max=_parse_salary(job.salary_range)[1],
        experience_required=job.experience_required,
        education_required=job.education_required,
        employment_type=job.employment_type,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


def _to_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return []
        # PostgreSQL text[] can come back like "{a,b}".
        if v.startswith("{") and v.endswith("}"):
            items = [item.strip().strip('"') for item in v[1:-1].split(",") if item.strip()]
            return items
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _parse_salary(salary_range: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    if not salary_range:
        return None, None
    try:
        match_range = re.match(r"^\$(\d+)-\$(\d+)$", salary_range)
        if match_range:
            return int(match_range.group(1)), int(match_range.group(2))
        match_plus = re.match(r"^\$(\d+)\+$", salary_range)
        if match_plus:
            return int(match_plus.group(1)), None
        match_range_nodollar = re.match(r"^(\d+)-(\d+)$", salary_range)
        if match_range_nodollar:
            return int(match_range_nodollar.group(1)), int(match_range_nodollar.group(2))
        match_plus_nodollar = re.match(r"^(\d+)\+$", salary_range)
        if match_plus_nodollar:
            return int(match_plus_nodollar.group(1)), None
    except Exception:
        pass
    return None, None


def _to_storage_list(value, db: Session):
    dialect = (db.bind.dialect.name if db.bind is not None else "").lower()
    is_postgres = dialect == "postgresql"
    if value is None:
        return [] if is_postgres else json.dumps([])
    if isinstance(value, list):
        return value if is_postgres else json.dumps(value)
    if isinstance(value, str):
        if is_postgres:
            parsed = _to_list(value)
            return parsed if isinstance(parsed, list) else []
        return value
    return [] if is_postgres else json.dumps([])


def _to_storage_embedding(value):
    if value is None:
        return None
    # Flatten nested list [[...]] → [...]
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            value = value[0]
        # Always serialize to JSON string for storage in a TEXT column
        return json.dumps(value)
    if isinstance(value, str):
        # Already serialized or a string representation
        return value
    return str(value)



def _extract_skills(raw_text: str) -> List[str]:
    known_skills = [
        "python", "fastapi", "django", "flask", "postgresql", "mysql", "mongodb",
        "docker", "kubernetes", "aws", "azure", "gcp", "redis", "celery",
        "react", "next.js", "typescript", "javascript", "java", "spring boot",
        "node.js", "git", "sqlalchemy", "pytest"
    ]
    text_lower = raw_text.lower()
    found = [skill for skill in known_skills if skill in text_lower]
    return found[:20]


def _parse_job_from_text(raw_text: str) -> JobDescriptionCreate:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0][:255] if lines else "Untitled Job"

    requirements_text = ""
    req_match = re.search(r"(requirements?|must have|qualifications?)\s*:?\s*(.+)", raw_text, re.IGNORECASE | re.DOTALL)
    if req_match:
        requirements_text = req_match.group(2).strip()

    employment_type = None
    text_lower = raw_text.lower()
    for option in ["full-time", "part-time", "contract", "internship"]:
        if option in text_lower:
            employment_type = option
            break

    experience_required = None
    exp_match = re.search(r"(\d+)\+?\s+years?", raw_text, re.IGNORECASE)
    if exp_match:
        try:
            experience_required = int(exp_match.group(1))
        except ValueError:
            experience_required = None

    location = None
    for loc in ["remote", "san francisco", "new york", "bangalore", "hybrid", "onsite"]:
        if loc in text_lower:
            location = loc.title()
            break

    required_skills = _extract_skills(raw_text)
    if not required_skills:
        required_skills = ["communication"]

    description = raw_text.strip()
    if len(description) < 50:
        description = f"{description}\n\nThis job description was created from plain text input."

    requirements = requirements_text.strip()
    if requirements and len(requirements) < 50:
        requirements = f"{requirements}. Please refer to the full job description for details."

    return JobDescriptionCreate(
        title=title if len(title) >= 5 else f"Role: {title}",
        description=description,
        requirements=requirements,
        responsibilities=None,
        required_skills=required_skills,
        preferred_skills=[],
        location=location,
        salary_min=None,
        salary_max=None,
        experience_required=experience_required,
        education_required=None,
        employment_type=employment_type,
        status="active",
    )


async def _create_job_internal(
    job_data: JobDescriptionCreate,
    db: Session,
    current_user: User
) -> JobDescriptionResponse:
    """Shared create pipeline for structured form and plain-text format."""
    # Map salary_min/max to salary_range
    salary_range = None
    if job_data.salary_min is not None and job_data.salary_max is not None:
        salary_range = f"${job_data.salary_min}-${job_data.salary_max}"
    elif job_data.salary_min is not None:
        salary_range = f"${job_data.salary_min}+"

    job = JobDescription(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        title=job_data.title,
        description=job_data.description,
        requirements=job_data.requirements,
        responsibilities=job_data.responsibilities,
        required_skills=_to_storage_list(job_data.required_skills, db),
        preferred_skills=_to_storage_list(job_data.preferred_skills, db),
        location=job_data.location,
        salary_range=salary_range,
        experience_required=job_data.experience_required,
        education_required=job_data.education_required,
        employment_type=job_data.employment_type,
        status=job_data.status or "draft"
    )

    # Generate embedding for semantic search
    try:
        job_text = job.to_text_for_embedding()
        embedding = await embedding_service.generate_embedding(job_text)
        if embedding:
            job.embedding = _to_storage_embedding(embedding)
    except Exception as e:
        logger.warning(f"Embedding generation failed for job create: {str(e)}")

    db.add(job)
    db.commit()
    db.refresh(job)

    # Invalidate cached analytics overview for this tenant
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass

    # Publish flow: auto-generate matches.
    if job.status == "active":
        try:
            await matching_service.generate_matches_for_job(
                job_id=str(job.id),
                db=db,
                tenant_id=str(current_user.tenant_id),
                limit=50
            )
        except Exception as e:
            # Do not fail job creation if matching fails.
            logger.warning(f"Auto match generation failed for job {job.id}: {e}")

    return JobDescriptionResponse(
        id=str(job.id),
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        responsibilities=job.responsibilities,
        required_skills=_to_list(job.required_skills),
        preferred_skills=_to_list(job.preferred_skills),
        location=job.location,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        experience_required=job.experience_required,
        education_required=job.education_required,
        employment_type=job.employment_type,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job description"""
    try:
        response = await _create_job_internal(job_data=job_data, db=db, current_user=current_user)
        logger.info(f"Job created: {response.title} by {current_user.email}")
        return response
    except Exception as e:
        db.rollback()
        logger.exception("Job creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating job"
        )


@router.post("/from-text", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_from_text(
    payload: JobDescriptionFromTextCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job from pasted plain-text job description."""
    try:
        parsed = _parse_job_from_text(payload.raw_text)
        if payload.status is not None:
            parsed.status = payload.status
        response = await _create_job_internal(job_data=parsed, db=db, current_user=current_user)
        logger.info(f"Job created from plain text: {response.title} by {current_user.email}")
        return response
    except Exception as e:
        db.rollback()
        logger.exception("Plain-text job creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating job from plain text"
        )


@router.get("/", response_model=JobDescriptionList)
async def list_jobs(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List job descriptions with pagination"""
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page and page_size must be greater than or equal to 1")
    if page_size > 500:
        raise HTTPException(status_code=400, detail="Page size cannot exceed 500")

    query = db.query(JobDescription).filter(
        JobDescription.tenant_id == current_user.tenant_id,
        JobDescription.deleted_at.is_(None)
    )
    
    if status_filter:
        query = query.filter(JobDescription.status == status_filter)
    
    total = query.count()
    offset = (page - 1) * page_size
    jobs = query.order_by(JobDescription.created_at.desc()).offset(offset).limit(page_size).all()
    
    items = [
        JobDescriptionResponse(
            id=str(job.id),
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            required_skills=_to_list(job.required_skills),
            preferred_skills=_to_list(job.preferred_skills),
            location=job.location,
            salary_min=_parse_salary(job.salary_range)[0],
            salary_max=_parse_salary(job.salary_range)[1],
            experience_required=job.experience_required,
            education_required=job.education_required,
            employment_type=job.employment_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        for job in jobs
    ]
    
    return JobDescriptionList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{job_id}", response_model=JobDescriptionResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job by ID"""
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.tenant_id == current_user.tenant_id,
        JobDescription.deleted_at.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobDescriptionResponse(
        id=str(job.id),
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        responsibilities=job.responsibilities,
        required_skills=_to_list(job.required_skills),
        preferred_skills=_to_list(job.preferred_skills),
        location=job.location,
        salary_min=_parse_salary(job.salary_range)[0],
        salary_max=_parse_salary(job.salary_range)[1],
        experience_required=job.experience_required,
        education_required=job.education_required,
        employment_type=job.employment_type,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.patch("/{job_id}", response_model=JobDescriptionResponse)
async def update_job(
    job_id: str,
    job_data: JobDescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job description"""
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.tenant_id == current_user.tenant_id,
        JobDescription.deleted_at.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Map schema fields to model fields
        update_data = job_data.model_dump(exclude_unset=True)
        
         
        
        # Handle salary range merging
        min_bound = None
        max_bound = None
        
        # 1. Parse existing bounds from current job.salary_range
        if job.salary_range:
            match_range = re.match(r"^\$(\d+)-\$(\d+)$", job.salary_range)
            if match_range:
                min_bound = int(match_range.group(1))
                max_bound = int(match_range.group(2))
            else:
                match_plus = re.match(r"^\$(\d+)\+$", job.salary_range)
                if match_plus:
                    min_bound = int(match_plus.group(1))

        # 2. Merge with update parameters if present
        if 'salary_min' in update_data or 'salary_max' in update_data:
            salary_min_payload = update_data.pop('salary_min', None)
            salary_max_payload = update_data.pop('salary_max', None)
            
            if 'salary_min' in job_data.model_fields_set:
                min_bound = salary_min_payload
            if 'salary_max' in job_data.model_fields_set:
                max_bound = salary_max_payload

            # Construct new salary_range
            if min_bound is not None and max_bound is not None:
                update_data['salary_range'] = f"${min_bound}-${max_bound}"
            elif min_bound is not None:
                update_data['salary_range'] = f"${min_bound}+"
            else:
                update_data['salary_range'] = None
        
        for field, value in update_data.items():
            if field in {"required_skills", "preferred_skills"}:
                value = _to_storage_list(value, db)
            setattr(job, field, value)

        # Regenerate embedding if job content changed
        embed_fields = {
            "title", "description", "requirements", "required_skills",
            "location", "experience_required"
        }
        if embed_fields.intersection(update_data.keys()):
            try:
                job_text = job.to_text_for_embedding()
                embedding = await embedding_service.generate_embedding(job_text)
                if embedding:
                    job.embedding = _to_storage_embedding(embedding)
            except Exception as e:
                logger.warning(f"Embedding generation failed for job update: {str(e)}")
        
        db.commit()
        db.refresh(job)
        
        # Invalidate cached analytics overview for this tenant
        try:
            from app.routers.analytics import invalidate_analytics_cache
            invalidate_analytics_cache(str(current_user.tenant_id))
        except Exception:
            pass
        
        logger.info(f"Job updated: {job.title} by {current_user.email}")
        
        return JobDescriptionResponse(
            id=str(job.id),
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            required_skills=_to_list(job.required_skills),
            preferred_skills=_to_list(job.preferred_skills),
            location=job.location,
            salary_min=min_bound,
            salary_max=max_bound,
            experience_required=job.experience_required,
            education_required=job.education_required,
            employment_type=job.employment_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except Exception as e:
        db.rollback()
        logger.exception("Job update failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating job"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a job description"""
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.tenant_id == current_user.tenant_id,
        JobDescription.deleted_at.is_(None)
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        from datetime import datetime
        job.deleted_at = datetime.utcnow()
        db.commit()
        
        # Invalidate cached analytics overview for this tenant
        try:
            from app.routers.analytics import invalidate_analytics_cache
            invalidate_analytics_cache(str(current_user.tenant_id))
        except Exception:
            pass
        
        logger.info(f"Job deleted: {job.title} by {current_user.email}")
        return None
        
    except Exception as e:
        db.rollback()
        logger.exception("Job deletion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting job"
        )
