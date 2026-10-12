import logging

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.config import settings
from app.db.redis import redis_client

logger = logging.getLogger(__name__)


def login_rate_limit(request: Request) -> None:
    limit = settings.LOGIN_RATE_LIMIT_ATTEMPTS
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS

    if limit <= 0:
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:login:{client_ip}"

    try:
        pipeline = redis_client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window, nx=True)
        pipeline.ttl(key)
        attempts, _, ttl = pipeline.execute()
    except RedisError:
        logger.warning("Login rate limiter unavailable (Redis error); allowing request")
        return

    if attempts > limit:
        retry_after = ttl if isinstance(ttl, int) and ttl > 0 else window
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
