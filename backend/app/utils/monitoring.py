"""
Application Monitoring and Error Tracking with Sentry

This module provides Sentry integration for error tracking and performance monitoring.
Includes PII sanitization and context enrichment.

Features:
- Automatic error capture with context
- PII sanitization (emails, IPs, tokens)
- Tenant and user context tracking
- Performance monitoring
- Breadcrumb logging
"""

import logging
import re
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

logger = logging.getLogger(__name__)

# Check if Sentry is installed
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not installed. Error tracking will be disabled.")


def is_sentry_configured() -> bool:
    """Check if Sentry is configured and available"""
    return SENTRY_AVAILABLE and bool(settings.SENTRY_DSN)


def sanitize_pii(data: Any) -> Any:
    """
    Remove or mask PII from data before sending to Sentry.
    
    Sanitizes:
    - Email addresses
    - IP addresses
    - JWT tokens
    - Passwords
    - Credit card numbers
    
    Args:
        data: Data to sanitize (str, dict, list, or primitive)
    
    Returns:
        Sanitized copy of data
    """
    if isinstance(data, str):
        # Mask email addresses
        data = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            data
        )
        
        # Mask IP addresses
        data = re.sub(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            '[IP]',
            data
        )
        
        # Mask JWT tokens
        data = re.sub(
            r'Bearer\s+[\w-]+\.[\w-]+\.[\w-]+',
            'Bearer [TOKEN]',
            data
        )
        
        # Mask potential API keys or tokens
        if len(data) > 20 and re.match(r'^[A-Za-z0-9_-]+$', data):
            data = f"[TOKEN:{data[:4]}...{data[-4:]}]"
        
        return data
    
    elif isinstance(data, dict):
        sanitized = {}
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret',
            'authorization', 'credit_card', 'ssn'
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_pii(value)
        
        return sanitized
    
    elif isinstance(data, (list, tuple)):
        return [sanitize_pii(item) for item in data]
    
    else:
        return data


def init_sentry():
    """
    Initialize Sentry SDK with FastAPI integration.
    
    Configuration:
    - DSN from environment variable
    - PII sanitization enabled
    - Performance monitoring
    - Environment and release tracking
    """
    if not is_sentry_configured():
        logger.info("Sentry not configured or unavailable")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.VERSION}",
            
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
            ],
            
            # Performance monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            
            # Error sampling
            sample_rate=1.0,
            
            # PII sanitization
            before_send=before_send_event,
            before_breadcrumb=before_breadcrumb,
            
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Disable automatic PII
            max_breadcrumbs=50,
            debug=settings.DEBUG,
        )
        
        logger.info(f"Sentry initialized: {settings.ENVIRONMENT}@{settings.VERSION}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_event(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process event before sending to Sentry.
    
    - Sanitizes PII from exception messages and request data
    - Adds custom context
    - Filters out known non-critical errors
    
    Args:
        event: Sentry event dict
        hint: Additional context
    
    Returns:
        Modified event or None to drop the event
    """
    # Sanitize exception messages
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            if 'value' in exception:
                exception['value'] = sanitize_pii(exception['value'])
    
    # Sanitize request data
    if 'request' in event:
        if 'data' in event['request']:
            event['request']['data'] = sanitize_pii(event['request']['data'])
        if 'headers' in event['request']:
            event['request']['headers'] = sanitize_pii(event['request']['headers'])
        if 'cookies' in event['request']:
            event['request']['cookies'] = '[REDACTED]'
    
    # Sanitize extra context
    if 'extra' in event:
        event['extra'] = sanitize_pii(event['extra'])
    
    # Filter out specific errors
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            exc_type = exception.get('type', '')
            
            # Don't report expected HTTP exceptions
            if exc_type in ['HTTPException', 'StarletteHTTPException']:
                status_code = event.get('extra', {}).get('status_code', 500)
                if status_code < 500:
                    return None  # Drop client errors (4xx)
    
    return event


def before_breadcrumb(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process breadcrumb before adding to event.
    
    Sanitizes PII from breadcrumb data.
    
    Args:
        crumb: Breadcrumb dict
        hint: Additional context
    
    Returns:
        Modified breadcrumb or None to drop it
    """
    if 'message' in crumb:
        crumb['message'] = sanitize_pii(crumb['message'])
    
    if 'data' in crumb:
        crumb['data'] = sanitize_pii(crumb['data'])
    
    return crumb


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> None:
    """
    Manually capture an exception with optional context.
    
    Usage:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(e, context={"user_id": user.id})
    
    Args:
        error: Exception to capture
        context: Additional context dict
        level: Severity level (error, warning, info)
    """
    if not is_sentry_configured():
        logger.error(f"Exception (Sentry disabled): {error}", exc_info=True)
        return
    
    try:
        with sentry_sdk.push_scope() as scope:
            scope.level = level
            
            if context:
                sanitized_context = sanitize_pii(context)
                for key, value in sanitized_context.items():
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_exception(error)
    
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


class SentryContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enrich Sentry events with request context.
    
    Adds:
    - User information
    - Tenant context
    - Request metadata
    - Custom tags
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and enrich Sentry context"""
        
        if not is_sentry_configured():
            return await call_next(request)
        
        with sentry_sdk.push_scope() as scope:
            # Set request context
            scope.set_tag("endpoint", request.url.path)
            scope.set_tag("method", request.method)
            
            # Add user context if available
            if hasattr(request.state, "user"):
                user = request.state.user
                scope.set_user({
                    "id": str(user.id),
                    "email": sanitize_pii(user.email),
                    "tenant_id": str(user.tenant_id)
                })
                scope.set_tag("tenant_id", str(user.tenant_id))
            
            # Add custom context
            scope.set_extra("url", str(request.url))
            scope.set_extra("client_host", request.client.host if request.client else None)
            
            try:
                response = await call_next(request)
                
                # Tag response status
                scope.set_tag("status_code", response.status_code)
                
                return response
            
            except Exception as e:
                # Exception will be automatically captured by Sentry
                raise


# ============================================================================
# Utility Functions
# ============================================================================

def set_user_context(user_id: str, email: str, tenant_id: str):
    """
    Set user context for current Sentry scope.
    
    Args:
        user_id: User's unique identifier
        email: User's email (will be sanitized)
        tenant_id: Tenant identifier
    """
    if not is_sentry_configured():
        return
    
    sentry_sdk.set_user({
        "id": user_id,
        "email": sanitize_pii(email),
        "tenant_id": tenant_id
    })


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: Optional[Dict] = None):
    """
    Add a breadcrumb to the current Sentry scope.
    
    Breadcrumbs are used to track the sequence of events leading to an error.
    
    Args:
        message: Breadcrumb message
        category: Category (e.g., "auth", "db", "api")
        level: Severity level
        data: Additional data dict
    """
    if not is_sentry_configured():
        return
    
    sentry_sdk.add_breadcrumb(
        message=sanitize_pii(message),
        category=category,
        level=level,
        data=sanitize_pii(data) if data else None
    )
