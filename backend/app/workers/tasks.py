"""
Celery Background Tasks for Recruiting Platform

This module defines background tasks with proper session management
and tenant context isolation.

Features:
- Email sending tasks
- Data processing tasks
- Cleanup tasks
- Report generation
"""

import asyncio
import logging
from app.workers.celery_app import celery_app, DatabaseTask, TaskSessionManager

logger = logging.getLogger(__name__)


def _mask_email(email: str) -> str:
    """Return a privacy-safe email identifier for logging (never the full address)."""
    try:
        if "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        prefix = local[:2] if len(local) >= 2 else local
        return f"{prefix}***@{domain}"
    except Exception:
        return "***"


# ============================================================================
# Email Tasks
# ============================================================================

@celery_app.task(base=DatabaseTask, bind=True, name="app.workers.tasks.send_welcome_email")
def send_welcome_email(self, user_email: str, user_name: str):
    """
    Send welcome email to new user.

    Args:
        user_email: User's email address
        user_name: User's full name

    Example:
        send_welcome_email.delay("user@example.com", "John Doe")
    """
    masked = _mask_email(user_email)
    logger.info("Sending welcome email to %s", masked)

    try:
        # TODO: Implement actual email sending logic inside email_service
        raise NotImplementedError("send_welcome_email task is not yet fully implemented.")

    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", masked, e)
        raise self.retry(exc=e, countdown=60, max_retries=3)


# ============================================================================
# Data Processing Tasks
# ============================================================================

@celery_app.task(base=DatabaseTask, bind=True, name="app.workers.tasks.process_user_data")
def process_user_data(self, user_id: str):
    """
    Process user data in background.

    Args:
        user_id: User's unique identifier

    Example:
        process_user_data.delay("user-123")
    """
    logger.info("Processing data for user %s", user_id)

    async def _run():
        async with TaskSessionManager() as session:  # noqa: F841
            # TODO: fetch user and process data
            raise NotImplementedError("process_user_data task is not yet fully implemented.")

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("Failed to process data for user %s: %s", user_id, e)
        raise self.retry(exc=e, countdown=120, max_retries=3)


# ============================================================================
# Cleanup Tasks (Scheduled via Celery Beat)
# ============================================================================

@celery_app.task(base=DatabaseTask, bind=True, name="app.workers.tasks.cleanup_expired_sessions")
def cleanup_expired_sessions(self):
    """
    Clean up expired sessions from database.

    Scheduled task — runs periodically via Celery Beat.
    Exceptions are logged with full stack traces and retried properly.

    Example beat schedule:
        celery_app.conf.beat_schedule = {
            'cleanup-sessions': {
                'task': 'app.workers.tasks.cleanup_expired_sessions',
                'schedule': crontab(hour=2, minute=0),
            },
        }
    """
    logger.info("Starting session cleanup task")

    async def _run():
        async with TaskSessionManager() as session:  # noqa: F841
            # TODO: delete sessions older than N days
            raise NotImplementedError("cleanup_expired_sessions task is not yet fully implemented.")

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.exception("Session cleanup failed")
        raise self.retry(exc=e, countdown=300, max_retries=3) from e


# ============================================================================
# Report Generation Tasks
# ============================================================================

@celery_app.task(base=DatabaseTask, bind=True, name="app.workers.tasks.generate_report")
def generate_report(self, tenant_id: str, report_type: str):
    """
    Generate report for a tenant.

    Args:
        tenant_id: Tenant's unique identifier
        report_type: Type of report to generate

    Example:
        generate_report.apply_async(
            args=["tenant-123", "monthly"],
            headers={"tenant_id": "tenant-123"}
        )
    """
    logger.info("Generating %s report for tenant %s", report_type, tenant_id)

    async def _run():
        async with TaskSessionManager() as session:  # noqa: F841
            # TODO: query data, generate PDF, upload to storage
            raise NotImplementedError("generate_report task is not yet fully implemented.")

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("Failed to generate report for tenant %s: %s", tenant_id, e)
        raise self.retry(exc=e, countdown=300, max_retries=2)


# ============================================================================
# Celery Beat Schedule
# ============================================================================

celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions-daily": {
        "task": "app.workers.tasks.cleanup_expired_sessions",
        "schedule": 86400.0,  # every 24 hours
    },
}
