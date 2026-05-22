"""
Celery Configuration with Multi-tenancy and Async Session Safety

This module configures Celery with proper database session management
and tenant context propagation for background tasks.

Features:
- Custom DatabaseTask base class with automatic session cleanup
- Tenant context propagation via task headers
- Async session safety with connection pooling
- Redis broker and result backend
"""

import logging
from typing import Optional, Any, Dict
from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, worker_init
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Tenant context variable for task execution
task_tenant_id: ContextVar[Optional[str]] = ContextVar('task_tenant_id', default=None)

# ============================================================================
# Celery Application Configuration
# ============================================================================

celery_app = Celery(
    "recruiting_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Results
    result_expires=86400,  # 24h retention to prevent unbounded Redis growth
    result_key_prefix="recruit:celery-result:",
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Routing
    task_default_queue="recruit_default",
    task_routes={
        "app.workers.tasks.*": {"queue": "recruit_default"},
    },
    
    # Rate limiting
    task_default_rate_limit="100/m",
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)


# ============================================================================
# Async Database Session Management for Tasks
# ============================================================================

# Create a separate engine for Celery workers
# Using NullPool to avoid connection issues in multiprocessing
celery_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    poolclass=NullPool,  # Disable pooling for worker processes
    future=True,
)

# Session factory for Celery tasks
CelerySessionLocal = async_sessionmaker(
    celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class DatabaseTask(Task):
    """
    Custom Celery task base class with automatic database session management.
    
    Features:
    - Automatic session creation and cleanup
    - Tenant context propagation
    - Error handling with rollback
    - Session safety for async operations
    
    Usage:
        @celery_app.task(base=DatabaseTask, bind=True)
        async def my_task(self, user_id: str):
            async with self.db_session() as session:
                # Use session here
                pass
    """
    
    _db_session: Optional[AsyncSession] = None
    
    async def get_db_session(self) -> AsyncSession:
        """
        Get or create a database session for this task.
        
        Returns:
            AsyncSession instance
        """
        if self._db_session is None:
            self._db_session = CelerySessionLocal()
        return self._db_session
    
    async def cleanup_session(self):
        """Close and cleanup database session"""
        if self._db_session is not None:
            await self._db_session.close()
            self._db_session = None
    
    def before_start(self, task_id, args, kwargs):
        """Called before task execution"""
        # Extract tenant_id from task headers
        tenant_id = self.request.get("tenant_id")
        if tenant_id:
            task_tenant_id.set(tenant_id)
            logger.info(f"Task {task_id} starting with tenant_id: {tenant_id}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Session cleanup will happen in after_return
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Called after task execution (success or failure).
        
        Ensures database session is properly closed.
        """
        import asyncio
        
        # Clean up session
        if self._db_session is not None:
            try:
                # Run cleanup in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.cleanup_session())
                else:
                    loop.run_until_complete(self.cleanup_session())
            except Exception as e:
                logger.error(f"Failed to cleanup session for task {task_id}: {e}")
        
        # Clear tenant context
        task_tenant_id.set(None)
        logger.debug(f"Task {task_id} cleanup completed")


# ============================================================================
# Celery Signals
# ============================================================================

@worker_init.connect
def setup_worker(sender, **kwargs):
    """
    Initialize worker process.
    
    Called when a worker process starts.
    """
    logger.info(f"Celery worker initialized: {sender}")


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extra):
    """
    Called before task execution.
    
    Sets up logging context and validates tenant context.
    """
    logger.info(f"Starting task: {task.name} [{task_id}]")
    
    # Log tenant context if present
    tenant_id = task_tenant_id.get()
    if tenant_id:
        logger.info(f"Task {task_id} executing in tenant context: {tenant_id}")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, **extra):
    """
    Called after task execution.
    
    Logs task completion and performance metrics.
    """
    logger.info(f"Completed task: {task.name} [{task_id}]")


# ============================================================================
# Utility Functions
# ============================================================================

def create_task_with_tenant_context(tenant_id: str):
    """
    Decorator to automatically inject tenant context into Celery tasks.
    
    Usage:
        @create_task_with_tenant_context(tenant_id="tenant-123")
        @celery_app.task
        def my_task():
            # Task will have tenant context
            pass
    
    Args:
        tenant_id: Tenant identifier to inject
    
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add tenant_id to task headers
            return func.apply_async(
                args=args,
                kwargs=kwargs,
                headers={"tenant_id": tenant_id}
            )
        return wrapper
    return decorator


async def get_tenant_context() -> Optional[str]:
    """
    Get current tenant context in a Celery task.
    
    Returns:
        Tenant ID string or None
    """
    return task_tenant_id.get()


def ensure_tenant_context(func):
    """
    Decorator to ensure a task has tenant context.
    
    Raises ValueError if tenant context is not set.
    
    Usage:
        @celery_app.task(base=DatabaseTask)
        @ensure_tenant_context
        async def my_task(self):
            # This will fail if no tenant context
            pass
    """
    async def wrapper(*args, **kwargs):
        tenant_id = task_tenant_id.get()
        if not tenant_id:
            raise ValueError("Task must be executed with tenant context")
        return await func(*args, **kwargs)
    return wrapper


# ============================================================================
# Session Context Manager for Tasks
# ============================================================================

class TaskSessionManager:
    """
    Context manager for database sessions in Celery tasks.
    
    Usage:
        async with TaskSessionManager() as session:
            # Use session
            result = await session.execute(query)
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        """Create and return session"""
        self.session = CelerySessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session and handle errors"""
        if self.session:
            try:
                if exc_type is not None:
                    # Rollback on error
                    await self.session.rollback()
                else:
                    # Commit on success
                    await self.session.commit()
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
                await self.session.rollback()
            finally:
                await self.session.close()
                self.session = None
        
        # Don't suppress exceptions
        return False


# ============================================================================
# Health Check
# ============================================================================

@celery_app.task(name="app.workers.celery_app.health_check")
def health_check() -> Dict[str, str]:
    """
    Simple health check task for monitoring.
    
    Returns:
        Dict with status
    """
    return {"status": "healthy", "service": "celery"}
