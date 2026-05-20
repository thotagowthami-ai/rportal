"""
Rate Limiting Middleware and Dependencies with Redis Backend

This module implements rate limiting with a fail-open strategy for reliability.
Uses Redis for distributed rate limiting across application instances.

Features:
- Tier-based rate limits (free, pro, enterprise)
- IP-based and user-based rate limiting
- Custom rate limit headers
- Fail-open strategy (allows requests if Redis is unavailable)
"""

import time
import logging
from typing import Optional, Tuple
from functools import wraps
import redis.asyncio as redis
from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm.
    
    Implements fail-open strategy: if Redis fails, allows the request
    and logs the error rather than blocking legitimate traffic.
    """
    
    def __init__(self):
        """Initialize Redis connection pool"""
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            logger.info("Redis connection initialized for rate limiting")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, dict]:
        """
        Check if request should be rate limited using sliding window.
        
        Args:
            key: Unique identifier for rate limit bucket (e.g., "ip:192.168.1.1")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, headers_dict)
            - is_allowed: True if request should be allowed
            - headers_dict: Rate limit headers to include in response
        """
        if not self.redis_client:
            logger.warning("Redis unavailable, allowing request (fail-open)")
            return True, self._get_fallback_headers(max_requests)
        
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry on the key
            pipe.expire(key, window_seconds)
            
            # Execute pipeline
            results = await pipe.execute()
            request_count = results[1]  # Result of zcard
            
            # Calculate headers
            remaining = max(0, max_requests - request_count - 1)
            reset_time = int(current_time + window_seconds)
            
            headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
            
            is_allowed = request_count < max_requests
            
            if not is_allowed:
                headers["Retry-After"] = str(window_seconds)
                logger.warning(f"Rate limit exceeded for key: {key}")
            
            return is_allowed, headers
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}, allowing request (fail-open)")
            return True, self._get_fallback_headers(max_requests)
    
    def _get_fallback_headers(self, max_requests: int) -> dict:
        """Return fallback headers when Redis is unavailable"""
        return {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(max_requests),
            "X-RateLimit-Reset": str(int(time.time() + 3600))
        }
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add rate limit headers to all responses.
    
    Applies IP-based rate limiting to all endpoints unless
    user-specific rate limiting is applied at the endpoint level.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add rate limit headers"""
        
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Use IP-based rate limiting as default
        rate_limit_key = f"{settings.REDIS_KEY_PREFIX}rate_limit:ip:{client_ip}"
        max_requests = settings.RATE_LIMIT_PER_MINUTE
        window_seconds = 60
        
        # Check rate limit
        is_allowed, headers = await rate_limiter.check_rate_limit(
            rate_limit_key,
            max_requests,
            window_seconds
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
        
        return response


# ============================================================================
# Rate Limiting Dependencies
# ============================================================================

def get_rate_limit_tier(user_tier: Optional[str] = None) -> Tuple[int, int]:
    """
    Get rate limit configuration based on user tier.
    
    Args:
        user_tier: User's subscription tier (free, pro, enterprise)
    
    Returns:
        Tuple of (max_requests, window_seconds)
    """
    tier_limits = {
        "free": (100, 3600),      # 100 requests per hour
        "pro": (1000, 3600),      # 1000 requests per hour
        "enterprise": (10000, 3600)  # 10000 requests per hour
    }
    
    return tier_limits.get(user_tier or "free", tier_limits["free"])


async def check_user_rate_limit(
    request: Request,
    user_id: str,
    user_tier: str = "free"
) -> None:
    """
    Dependency to check user-specific rate limits.
    
    Usage:
        @app.get("/api/expensive-operation")
        async def expensive_op(
            current_user = Depends(get_current_user),
            _ = Depends(check_user_rate_limit)
        ):
            ...
    
    Args:
        request: FastAPI request object
        user_id: User's unique identifier
        user_tier: User's subscription tier
    
    Raises:
        HTTPException: If rate limit is exceeded
    """
    max_requests, window_seconds = get_rate_limit_tier(user_tier)
    rate_limit_key = f"{settings.REDIS_KEY_PREFIX}rate_limit:user:{user_id}"
    
    is_allowed, headers = await rate_limiter.check_rate_limit(
        rate_limit_key,
        max_requests,
        window_seconds
    )
    
    # Store headers in request state for middleware to add
    request.state.rate_limit_headers = headers
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="User rate limit exceeded. Please upgrade your plan or try again later.",
            headers=headers
        )


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator for endpoint-specific rate limiting.
    
    Usage:
        @app.get("/api/endpoint")
        @rate_limit(max_requests=10, window_seconds=60)
        async def my_endpoint():
            ...
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
                if request:
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_key = f"{settings.REDIS_KEY_PREFIX}rate_limit:endpoint:{func.__name__}:{client_ip}"
                
                is_allowed, headers = await rate_limiter.check_rate_limit(
                    rate_limit_key,
                    max_requests,
                    window_seconds
                )
                
                request.state.rate_limit_headers = headers
                
                if not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded for {func.__name__}",
                        headers=headers
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
