import redis
from app.config import settings
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service with tenant isolation.

    SECURITY: All cache keys are scoped by tenant_id to prevent
    cross-tenant data leakage through cache poisoning.
    """

    def __init__(self):
        self.in_memory_cache = {}
        # Make Redis OPTIONAL
        redis_url = getattr(settings, "REDIS_URL", None)

        if not redis_url:
            logger.warning("REDIS_URL not configured. Cache falling back to in-memory storage.")
            self.redis_client = None
        else:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                    socket_keepalive=True,
                    retry_on_timeout=False
                )
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}. Falling back to in-memory storage.")
                self.redis_client = None

    def _make_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        prefix = settings.REDIS_KEY_PREFIX
        if tenant_id:
            return f"{prefix}tenant:{tenant_id}:{key}"
        return f"{prefix}global:{key}"

    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        scoped_key = self._make_key(key, tenant_id)
        if not self.redis_client:
            from datetime import datetime
            entry = self.in_memory_cache.get(scoped_key)
            if entry:
                value, expires_at = entry
                if expires_at is None or expires_at > datetime.utcnow().timestamp():
                    try:
                        return json.loads(value)
                    except Exception:
                        return value
                else:
                    self.in_memory_cache.pop(scoped_key, None)
            return None

        try:
            value = self.redis_client.get(scoped_key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get failed for {key}: {str(e)}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None
    ) -> bool:
        scoped_key = self._make_key(key, tenant_id)
        if not self.redis_client:
            from datetime import datetime
            serialized = json.dumps(value)
            expires_at = datetime.utcnow().timestamp() + ttl if ttl is not None and ttl > 0 else None
            self.in_memory_cache[scoped_key] = (serialized, expires_at)
            return True

        try:
            serialized = json.dumps(value)
            if ttl is not None and ttl > 0:
                self.redis_client.setex(scoped_key, ttl, serialized)
            else:
                self.redis_client.set(scoped_key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {str(e)}")
            return False

    def delete(self, key: str, tenant_id: Optional[str] = None) -> bool:
        scoped_key = self._make_key(key, tenant_id)
        if not self.redis_client:
            self.in_memory_cache.pop(scoped_key, None)
            return True

        try:
            self.redis_client.delete(scoped_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {str(e)}")
            return False


# Global instance (safe now)
cache_service = CacheService()