"""Redis-backed JWT token blacklist for revoked tokens."""

import redis.asyncio as redis


class RedisTokenBlacklist:
    """Stores revoked JWT token IDs in Redis with TTL expiration."""

    def __init__(self, redis_url: str) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def blacklist(self, jti: str, expires_in: int) -> None:
        await self._redis.setex(f"token_blacklist:{jti}", expires_in, "1")

    async def is_blacklisted(self, jti: str) -> bool:
        result = await self._redis.get(f"token_blacklist:{jti}")
        return result is not None

    async def close(self) -> None:
        await self._redis.aclose()
