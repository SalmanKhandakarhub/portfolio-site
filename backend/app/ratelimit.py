"""Per-IP rate limiting.

Deliberately backed by Redis rather than a dict: with several Uvicorn
workers, an in-process counter is per-worker, so a limit of 3 quietly
becomes 3 x workers. Redis gives one shared counter.

If Redis is unreachable the limiter fails OPEN — a broken cache should not
stop real people contacting you. Spam is cheaper than a silent outage.
"""

import logging

from redis.asyncio import Redis, from_url

from .config import settings

log = logging.getLogger("contact.ratelimit")

_redis: Redis | None = None


async def init_redis() -> None:
    global _redis
    try:
        client = from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        _redis = client
        log.info("rate limiter connected to Redis")
    except Exception:
        _redis = None
        log.warning("Redis unavailable — rate limiting disabled", exc_info=True)


async def close_redis() -> None:
    if _redis is not None:
        await _redis.aclose()


async def too_many(ip: str) -> bool:
    """True if this IP has already used up its allowance."""
    if _redis is None:
        return False

    key = f"contact:rl:{ip}"
    try:
        # INCR then EXPIRE only on first hit, so the window is fixed from
        # the first request rather than sliding forward with each one.
        count = await _redis.incr(key)
        if count == 1:
            await _redis.expire(key, settings.RATE_LIMIT_WINDOW)
        return count > settings.RATE_LIMIT_MAX
    except Exception:
        log.warning("rate limit check failed for %s", ip, exc_info=True)
        return False


def client_ip(request) -> str:
    """Real client address behind nginx and a load balancer.

    X-Forwarded-For is a chain: client, proxy1, proxy2. The leftmost entry
    is the client, but it is also the one a caller can forge — trust it only
    because nginx and the ALB sit in front and rewrite the header.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
