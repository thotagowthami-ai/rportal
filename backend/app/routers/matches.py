from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.models.match import Match
from app.models.job_description import JobDescription
from app.schemas.match import MatchResponse, MatchList, MatchUpdate, MatchGenerateSelectedRequest
from app.services.matching_service import matching_service
import math
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches", tags=["Matches"])


def _to_match_response(match: Match) -> MatchResponse:
    return MatchResponse(
        id=str(match.id),
        job_description_id=str(match.job_description_id),
        resume_id=str(match.resume_id),
        overall_score=match.overall_score,
        skill_match_score=match.skill_match_score,
        experience_match_score=match.experience_match_score,
        education_match_score=match.education_match_score,
        matched_skills=match.matched_skills,
        missing_skills=match.missing_skills,
        match_reasoning=match.match_reasoning,
        recruiter_status=(str(match.recruiter_status).lower() if match.recruiter_status else "new"),
        recruiter_notes=match.recruiter_notes,
        reviewed_at=match.reviewed_at,
        created_at=match.created_at
    )


# FIXED: Changed from /generate/{job_id} to /generate with query param
@router.post("/generate", response_model=MatchList, status_code=status.HTTP_201_CREATED)
async def generate_matches(
    job_id: str = Query(..., description="Job ID to generate matches for"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate matches for a job description.
    Usage: POST /api/matches/generate?job_id=xxx&limit=50
    """
    try:
        matches = await matching_service.generate_matches_for_job(
            job_id=job_id,
            db=db,
            tenant_id=str(current_user.tenant_id),
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Match generation failed")
        error_msg = str(e).lower()
        if "image" in error_msg or "model does not support" in error_msg:
            raise HTTPException(status_code=400, detail="Unable to process candidate data. Please try again later.")
        raise HTTPException(status_code=500, detail="Match generation failed")

    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass
    items = [_to_match_response(m) for m in matches]
    return MatchList(
        items=items,
        total=len(items),
        page=1,
        page_size=len(items),
        total_pages=1
    )


@router.post("/generate-selected", response_model=MatchList, status_code=status.HTTP_201_CREATED)
async def generate_matches_for_selected_resumes(
    payload: MatchGenerateSelectedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate matches for one job against selected resume IDs only.
    """
    try:
        matches = await matching_service.generate_matches_for_job(
            job_id=payload.job_id,
            db=db,
            tenant_id=str(current_user.tenant_id),
            limit=payload.limit,
            resume_ids=payload.resume_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Selected match generation failed")
        error_msg = str(e).lower()
        if "image" in error_msg or "model does not support" in error_msg:
            raise HTTPException(status_code=400, detail="Unable to process candidate data. Please try again later.")
        raise HTTPException(status_code=500, detail="Selected match generation failed")

    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass
    items = [_to_match_response(m) for m in matches]
    return MatchList(
        items=items,
        total=len(items),
        page=1,
        page_size=len(items),
        total_pages=1
    )


# FIXED: Changed from /job/{job_id} to /job with query param
@router.get("/job", response_model=MatchList)
async def list_matches_for_job(
    job_id: str = Query(..., description="Job ID to list matches for"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List matches for a job with pagination.
    Usage: GET /api/matches/job?job_id=xxx&page=1&page_size=20
    """
    query = db.query(Match).filter(
        Match.job_description_id == job_id,
        Match.tenant_id == current_user.tenant_id
    )

    if status_filter:
        query = query.filter(Match.recruiter_status == status_filter.upper())

    total = query.count()
    offset = (page - 1) * page_size
    matches = (
        query.order_by(Match.overall_score.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [_to_match_response(m) for m in matches]
    return MatchList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/resume")
async def list_matches_for_resume(
    resume_id: str = Query(..., description="Resume ID to list matches for"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = (
        db.query(Match, JobDescription.title.label("job_title"), JobDescription.status.label("job_status"))
        .join(JobDescription, Match.job_description_id == JobDescription.id)
        .filter(
            Match.resume_id == resume_id,
            Match.tenant_id == current_user.tenant_id,
            JobDescription.tenant_id == current_user.tenant_id,
        )
    )

    total = query.count()
    offset = (page - 1) * page_size
    rows = (
        query.order_by(Match.overall_score.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "id": str(match.id),
            "job_description_id": str(match.job_description_id),
            "resume_id": str(match.resume_id),
            "overall_score": match.overall_score,
            "skill_match_score": match.skill_match_score,
            "experience_match_score": match.experience_match_score,
            "education_match_score": match.education_match_score,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
            "match_reasoning": match.match_reasoning,
            "recruiter_status": str(match.recruiter_status).lower() if match.recruiter_status else "new",
            "recruiter_notes": match.recruiter_notes,
            "created_at": match.created_at,
            "job_title": job_title,
            "job_status": str(job_status).lower() if job_status else None,
        }
        for match, job_title, job_status in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: str,
    update: MatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update recruiter status/notes for a match.
    """
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.tenant_id == current_user.tenant_id
    ).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    update_data = update.model_dump(exclude_unset=True)
    if "recruiter_status" in update_data and update_data["recruiter_status"] is not None:
        update_data["recruiter_status"] = update_data["recruiter_status"].upper()
    for field, value in update_data.items():
        setattr(match, field, value)

    if "recruiter_status" in update_data:
        match.reviewed_by = current_user.id
        match.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(match)
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(str(current_user.tenant_id))
    except Exception:
        pass
    return _to_match_response(match)
