import json
import logging
from typing import Any
from uuid import UUID

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = redis.from_url(self._redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def get_json(self, key: str) -> Any | None:
        if self._redis is None:
            return None
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._redis is None:
            return
        await self._redis.set(key, json.dumps(value), ex=ttl)

    async def invalidate_prefix_utilization(self, prefix_id: UUID) -> None:
        if self._redis is None:
            return
        key = f"prefix_utilization:{prefix_id}"
        await self._redis.delete(key)
