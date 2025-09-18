"""
Redis caching service for performance optimization.
"""
import json
import logging
import asyncio
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for performance optimization"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = settings.redis_url
        self.default_ttl = 3600  # 1 hour default TTL
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                # Cloud endpoints can be slower to handshake
                socket_connect_timeout=3.0,
                socket_timeout=3.0,
                health_check_interval=30,
                retry_on_timeout=True,
            )
            # Test connection
            try:
                # Ensure ping does not block startup for long
                await asyncio.wait_for(self.redis_client.ping(), timeout=1.0)
            except Exception as ping_err:
                logger.warning(f"Redis ping failed or timed out: {ping_err}")
                # Treat as non-fatal; proceed without Redis
                self.redis_client = None
                return
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        fetch_func, 
        ttl: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """Get from cache or fetch and set if not exists"""
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Fetch from source
        try:
            value = await fetch_func(*args, **kwargs)
            if value is not None:
                await self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {str(e)}")
            raise
    
    def generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)


# Cache key prefixes
class CacheKeys:
    USER = "user"
    USER_BY_EMAIL = "user:email"
    USER_BY_USERNAME = "user:username"
    USER_BY_ID = "user:id"
    CLASS = "class"
    CLASS_BY_TEACHER = "class:teacher"
    AUDIO_RECORDING = "audio"
    AUDIO_BY_CLASS = "audio:class"
    LESSON_SUMMARY = "summary"
    REFRESH_TOKEN = "refresh_token"
    EMBEDDING = "embedding"


# Global cache service instance
cache_service = CacheService()


# Cache decorators
def cache_result(prefix: str, ttl: int = 3600, key_args: list = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_args:
                cache_key = cache_service.generate_key(prefix, *[kwargs.get(arg) for arg in key_args])
            else:
                cache_key = cache_service.generate_key(prefix, *args)
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(patterns: list):
    """Decorator to invalidate cache patterns after function execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache patterns
            for pattern in patterns:
                await cache_service.delete_pattern(pattern)
            
            return result
        return wrapper
    return decorator
