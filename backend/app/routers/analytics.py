from datetime import datetime, timedelta
import json
import logging

from fastapi import APIRouter, Depends, Query
from redis.exceptions import RedisError
from sqlalchemy import String, case, cast, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.job_description import JobDescription
from app.models.match import Match
from app.models.resume import Resume
from app.models.user import User
from app.core.redis_client import redis_client
from app.config import settings

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id

    jobs_count = (
        db.query(JobDescription)
        .filter(
            JobDescription.tenant_id == tenant_id,
            JobDescription.deleted_at.is_(None),
        )
        .count()
    )
    resumes_count = (
        db.query(Resume)
        .filter(
            Resume.tenant_id == tenant_id,
            Resume.deleted_at.is_(None),
        )
        .count()
    )
    matches_count = (
        db.query(Match)
        .filter(Match.tenant_id == tenant_id)
        .count()
    )

    recent_jobs_query = (
        db.query(
            JobDescription.id,
            JobDescription.title,
            JobDescription.status,
            JobDescription.location,
            func.count(Match.id).label("matches_count"),
        )
        .outerjoin(Match, Match.job_description_id == JobDescription.id)
        .filter(
            JobDescription.tenant_id == tenant_id,
            JobDescription.deleted_at.is_(None),
        )
        .group_by(
            JobDescription.id,
            JobDescription.title,
            JobDescription.status,
            JobDescription.location,
        )
        .order_by(JobDescription.created_at.desc())
        .limit(5)
        .all()
    )

    recent_jobs = [
        {
            "id": str(job.id),
            "title": job.title,
            "status": job.status,
            "location": job.location,
            "matches_count": int(job.matches_count or 0),
        }
        for job in recent_jobs_query
    ]

    latest_job_events = (
        db.query(
            JobDescription.id,
            JobDescription.title,
            JobDescription.created_at,
        )
        .filter(
            JobDescription.tenant_id == tenant_id,
            JobDescription.deleted_at.is_(None),
        )
        .order_by(JobDescription.created_at.desc())
        .limit(5)
        .all()
    )

    latest_resume_events = (
        db.query(
            Resume.id,
            Resume.candidate_name,
            Resume.created_at,
        )
        .filter(
            Resume.tenant_id == tenant_id,
            Resume.deleted_at.is_(None),
        )
        .order_by(Resume.created_at.desc())
        .limit(5)
        .all()
    )

    latest_match_events = (
        db.query(
            Match.id,
            Match.created_at,
            Match.overall_score,
            JobDescription.id.label("job_id"),
            JobDescription.title.label("job_title"),
        )
        .join(JobDescription, Match.job_description_id == JobDescription.id)
        .filter(Match.tenant_id == tenant_id)
        .order_by(Match.created_at.desc())
        .limit(5)
        .all()
    )

    activity_items = []

    for event in latest_job_events:
        activity_items.append(
            {
                "type": "job_created",
                "message": f'Created job "{event.title}"',
                "timestamp": event.created_at or datetime.utcnow(),
                "link": f"/jobs/{event.id}",
            }
        )

    for event in latest_resume_events:
        activity_items.append(
            {
                "type": "resume_uploaded",
                "message": f'Uploaded resume "{event.candidate_name}"',
                "timestamp": event.created_at or datetime.utcnow(),
                "link": f"/resumes/{event.id}",
            }
        )

    for event in latest_match_events:
        score_text = (
            f"{event.overall_score:.1f}%"
            if event.overall_score is not None
            else "pending"
        )
        activity_items.append(
            {
                "type": "match_generated",
                "message": f'Generated {score_text} match for "{event.job_title}"',
                "timestamp": event.created_at or datetime.utcnow(),
                "link": f"/jobs/{event.job_id}",
            }
        )

    latest_activity = sorted(activity_items, key=lambda item: item["timestamp"], reverse=True)[:8]
    latest_activity_response = [
        {
            "type": item["type"],
            "message": item["message"],
            "timestamp": item["timestamp"].isoformat(),
            "link": item["link"],
        }
        for item in latest_activity
    ]

    return {
        "jobs_count": jobs_count,
        "resumes_count": resumes_count,
        "matches_count": matches_count,
        "recent_jobs": recent_jobs,
        "latest_activity": latest_activity_response,
    }


@router.get("/overview")
def get_analytics_overview(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = str(current_user.tenant_id)
    now = datetime.utcnow()
    period_start = now - timedelta(days=days)
    prev_start = period_start - timedelta(days=days)
    cache_key = f"{settings.REDIS_KEY_PREFIX}analytics:overview:{tenant_id}:{days}"
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except (RedisError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Analytics cache read failed for key=%s: %s", cache_key, exc)

    jobs_query = db.query(JobDescription).filter(
        JobDescription.tenant_id == tenant_id,
        JobDescription.deleted_at.is_(None),
    )
    resumes_query = db.query(Resume).filter(
        Resume.tenant_id == tenant_id,
        Resume.deleted_at.is_(None),
    )
    matches_query = db.query(Match).filter(Match.tenant_id == tenant_id)

    active_jobs = jobs_query.filter(JobDescription.status == "active").count()
    total_candidates = resumes_query.count()
    total_matches = matches_query.count()

    jobs_current = jobs_query.filter(JobDescription.created_at >= period_start).count()
    jobs_prev = jobs_query.filter(
        JobDescription.created_at >= prev_start,
        JobDescription.created_at < period_start,
    ).count()
    candidates_current = resumes_query.filter(Resume.created_at >= period_start).count()
    candidates_prev = resumes_query.filter(
        Resume.created_at >= prev_start,
        Resume.created_at < period_start,
    ).count()

    status_text = cast(Match.recruiter_status, String)

    reviewed_count = matches_query.filter(func.lower(status_text) != "new").count()
    shortlisted_count = matches_query.filter(func.lower(status_text) == "shortlisted").count()
    interviewed_count = matches_query.filter(func.lower(status_text) == "interviewed").count()
    offered_count = matches_query.filter(func.lower(status_text) == "offered").count()

    response_rate = round((reviewed_count / total_matches) * 100, 1) if total_matches else 0.0

    top_jobs_rows = (
        db.query(
            JobDescription.id,
            JobDescription.title,
            JobDescription.created_at,
            func.count(Match.id).label("matches_count"),
            func.sum(case((func.lower(cast(Match.recruiter_status, String)) == "shortlisted", 1), else_=0)).label("shortlisted_count"),
        )
        .outerjoin(Match, Match.job_description_id == JobDescription.id)
        .filter(
            JobDescription.tenant_id == tenant_id,
            JobDescription.deleted_at.is_(None),
        )
        .group_by(JobDescription.id, JobDescription.title, JobDescription.created_at)
        .order_by(func.count(Match.id).desc())
        .limit(10)
        .all()
    )

    top_jobs = []
    for row in top_jobs_rows:
        days_open = max(0, (now - row.created_at).days) if row.created_at else 0
        top_jobs.append(
            {
                "job_id": str(row.id),
                "title": row.title,
                "matches": int(row.matches_count or 0),
                "shortlisted": int(row.shortlisted_count or 0),
                "days_open": int(days_open),
            }
        )

    weekly_points = []
    for i in range(4):
        end = now - timedelta(days=i * 7)
        start = end - timedelta(days=7)
        avg_score = (
            db.query(func.avg(Match.overall_score))
            .filter(
                Match.tenant_id == tenant_id,
                Match.created_at >= start,
                Match.created_at < end,
            )
            .scalar()
        )
        weekly_points.append(
            {
                "label": f"Week {4 - i}",
                "avg_score": round(float(avg_score), 1) if avg_score is not None else 0.0,
            }
        )
    weekly_points.reverse()

    time_to_hire_days = []
    jobs_with_offer = (
        db.query(
            JobDescription.created_at.label("job_created_at"),
            Match.reviewed_at.label("reviewed_at"),
            Match.recruiter_status.label("status"),
            Match.job_description_id.label("job_id"),
        )
        .join(JobDescription, Match.job_description_id == JobDescription.id)
        .filter(
            JobDescription.tenant_id == tenant_id,
            JobDescription.deleted_at.is_(None),
            Match.reviewed_at.isnot(None),
            func.lower(cast(Match.recruiter_status, String)).in_(["offered", "interviewed", "shortlisted"]),
        )
        .order_by(Match.job_description_id, Match.reviewed_at.asc())
        .all()
    )

    first_seen_by_job = {}
    for row in jobs_with_offer:
        if row.job_id in first_seen_by_job:
            continue
        first_seen_by_job[row.job_id] = row

    for row in first_seen_by_job.values():
        if row.job_created_at and row.reviewed_at:
            days_diff = max(0, (row.reviewed_at - row.job_created_at).days)
            time_to_hire_days.append(days_diff)

    avg_hire = round(sum(time_to_hire_days) / len(time_to_hire_days), 1) if time_to_hire_days else 0.0
    fastest = min(time_to_hire_days) if time_to_hire_days else 0
    slowest = max(time_to_hire_days) if time_to_hire_days else 0

    response_data = {
        "days": days,
        "overview": {
            "active_jobs": active_jobs,
            "total_candidates": total_candidates,
            "matches_generated": total_matches,
            "response_rate": response_rate,
            "jobs_delta": jobs_current - jobs_prev,
            "candidates_delta": candidates_current - candidates_prev,
        },
        "funnel": {
            "matches": total_matches,
            "reviewed": reviewed_count,
            "shortlisted": shortlisted_count,
            "interviewed": interviewed_count,
            "offered": offered_count,
        },
        "top_jobs": top_jobs,
        "quality_trend": weekly_points,
        "time_to_hire": {
            "average_days": avg_hire,
            "fastest_days": fastest,
            "slowest_days": slowest,
        },
    }

    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(response_data), ex=3600)
        except RedisError as exc:
            logger.warning("Analytics cache write failed for key=%s: %s", cache_key, exc)
    return response_data


def invalidate_analytics_cache(tenant_id: str) -> None:
    """
    Invalidate the analytics overview cache for a specific tenant.
    
    Scans and deletes all cache keys matching the pattern:
    {settings.REDIS_KEY_PREFIX}analytics:overview:{tenant_id}:*
    """
    pattern = f"{settings.REDIS_KEY_PREFIX}analytics:overview:{tenant_id}:*"
    if not redis_client:
        return
    try:
        # Non-blocking SCAN to find and delete keys matching the pattern securely
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.warning(
            "Failed to invalidate analytics cache for tenant %s: %s", tenant_id, e
        )

