"""
Redis-backed rate limiting middleware (simple token bucket in Redis).
"""
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import redis.asyncio as redis
from app.config import settings
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3.0,
            socket_timeout=3.0,
            health_check_interval=30,
            retry_on_timeout=True,
        )

    async def _acquire(self, key: str, max_per_minute: int) -> bool:
        now = int(time.time())
        window = now // 60
        redis_key = f"ratelimit:{key}:{window}"
        # Use INCR + EXPIRE for fixed window limiting
        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, 70)
        return count <= max_per_minute

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.headers.get("x-real-ip") or request.client.host if request.client else "unknown"

        # Buckets
        if path.startswith("/api/v1/auth/"):
            limit = 5
            bucket = "auth"
        elif path.startswith("/api/v1/audio/") or path.startswith("/api/v1/s3/"):
            limit = 10
            bucket = "upload"
        elif path in ("/docs", "/redoc", "/openapi.json", "/livez", "/readyz"):
            limit = None
            bucket = None
        else:
            limit = 60
            bucket = "general"

        if limit is None:
            return await call_next(request)

        key = f"{bucket}:{client_ip}"
        try:
            allowed = await self._acquire(key, limit)
        except Exception as ex:
            logger.warning(f"Rate limit redis error: {ex}")
            allowed = True

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Too many requests",
                        "details": f"Rate limit exceeded for {bucket}",
                        "type": "RateLimitExceeded"
                    }
                },
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)
        return response
