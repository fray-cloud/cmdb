"""Redis-backed login rate limiter to prevent brute-force attacks."""

import redis.asyncio as redis


class LoginRateLimiter:
    """Tracks failed login attempts and applies progressive lockouts."""

    THRESHOLDS = [
        (5, 300),  # 5 failures -> 5 min lockout
        (10, 1800),  # 10 failures -> 30 min lockout
    ]

    def __init__(self, redis_url: str) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def _key(self, email: str, ip: str) -> str:
        return f"login_attempt:{email}:{ip}"

    async def is_locked(self, email: str, ip: str) -> bool:
        lock_key = f"login_lock:{email}:{ip}"
        return await self._redis.exists(lock_key) > 0

    async def record_failure(self, email: str, ip: str) -> None:
        key = self._key(email, ip)
        count = await self._redis.incr(key)
        await self._redis.expire(key, 3600)

        for threshold, lockout_seconds in self.THRESHOLDS:
            if count == threshold:
                lock_key = f"login_lock:{email}:{ip}"
                await self._redis.setex(lock_key, lockout_seconds, "1")
                break

    async def reset(self, email: str, ip: str) -> None:
        key = self._key(email, ip)
        lock_key = f"login_lock:{email}:{ip}"
        await self._redis.delete(key, lock_key)

    async def close(self) -> None:
        await self._redis.aclose()
