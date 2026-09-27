import time
import asyncio
from collections import defaultdict, deque
from typing import Tuple, Optional
import redis.asyncio as aioredis
import logging

from aegis.config import settings

logger = logging.getLogger("aegis.rate_limiter")


class SlidingWindowRateLimiter:
    """
    Sliding-window rate limiter with Redis and in-memory implementations.
    Redis has finite connection timeouts; the in-memory fallback is process-local.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[aioredis.Redis] = None
        self._redis_available: bool = False
        self._last_redis_attempt = 0.0
        self._redis_retry_interval = 30.0  # seconds between reconnect attempts
        self._redis_lock = asyncio.Lock()

        # In-memory sliding window fallback: key -> deque of timestamps
        self._memory_store: dict[str, deque[float]] = defaultdict(deque)
        self._memory_lock = asyncio.Lock()

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        if not settings.REDIS_ENABLED:
            return None
        if self._redis is not None and self._redis_available:
            return self._redis

        now = time.time()
        if now - self._last_redis_attempt < self._redis_retry_interval:
            return None

        async with self._redis_lock:
            if self._redis is not None and self._redis_available:
                return self._redis
            if now - self._last_redis_attempt < self._redis_retry_interval:
                return None
            self._last_redis_attempt = now
            try:
                client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=0.2,  # Seconds; bounds time spent waiting on Redis
                    socket_connect_timeout=0.5
                )
                await client.ping()
                self._redis = client
                self._redis_available = True
                logger.info("Connected to Redis for sliding window rate limiting.")
                return self._redis
            except Exception as e:
                self._redis_available = False
                self._redis = None
                logger.debug(f"Redis unavailable ({e}), using in-memory sliding window fallback.")
                return None

    async def is_redis_connected(self) -> bool:
        """Check if Redis connection is active and responsive."""
        if not settings.REDIS_ENABLED:
            return False
        client = await self._get_redis()
        if client is None:
            return False
        try:
            return bool(await client.ping())
        except Exception:
            self._redis_available = False
            return False

    async def active_key_count(self) -> int:
        """Number of active sliding-window keys held by the memory fallback store."""
        return len(self._memory_store)

    def redis_connected(self) -> bool:
        """Synchronous snapshot of Redis connectivity state."""
        return bool(self._redis_available)

    async def check_velocity(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, int, float]:
        """
        Calculates requests in sliding window [now - window_seconds, now].
        Returns:
            (allowed: bool, current_count: int, retry_after_seconds: float)
        """
        now = time.time()
        window_start = now - window_seconds
        redis_client = await self._get_redis()

        if redis_client is not None:
            try:
                # Sliding window via atomic pipeline
                pipe = redis_client.pipeline(transaction=True)
                pipe.zremrangebyscore(key, "-inf", window_start)
                pipe.zcard(key)
                pipe.zadd(key, {f"{now}:{time.perf_counter_ns()}": now})
                pipe.expire(key, window_seconds + 5)
                results = await pipe.execute()

                # results[1] is the count before adding current request
                count = results[1] + 1
                allowed = count <= limit
                retry_after = float(window_seconds) if not allowed else 0.0
                return allowed, count, retry_after
            except Exception as e:
                logger.warning(f"Redis error during velocity check: {e}. Falling back to memory.")
                self._redis_available = False

        # In-Memory Fallback
        async with self._memory_lock:
            q = self._memory_store[key]
            # Evict timestamps outside sliding window
            while q and q[0] <= window_start:
                q.popleft()

            count = len(q) + 1
            if count <= limit:
                q.append(now)
                return True, count, 0.0
            else:
                earliest = q[0] if q else now
                retry_after = max(0.0, (earliest + window_seconds) - now)
                return False, count, retry_after

    async def reset(self, key: Optional[str] = None):
        """Reset rate limiter state (primarily for tests).

        A full Redis DB flush is intentionally not performed; only the in-memory
        fallback store is cleared when no explicit key is supplied.
        """
        async with self._memory_lock:
            if key:
                self._memory_store.pop(key, None)
            else:
                self._memory_store.clear()

        if key:
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    await redis_client.delete(key)
                except Exception:
                    pass


# Global singleton instance
rate_limiter = SlidingWindowRateLimiter()
