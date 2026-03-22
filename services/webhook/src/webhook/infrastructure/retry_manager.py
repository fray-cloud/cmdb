import json
import logging
import time
from dataclasses import dataclass

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class RetryItem:
    webhook_id: str
    event_payload: dict
    event_type: str
    attempt: int


class RetryManager:
    RETRY_KEY = "webhook:retries"

    def __init__(self, redis_url: str, max_retries: int = 5, backoffs: list[int] | None = None) -> None:
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._max_retries = max_retries
        self._backoffs = backoffs or [10, 30, 120, 600, 3600]

    async def connect(self) -> None:
        self._redis = redis.from_url(self._redis_url)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def schedule_retry(self, webhook_id: str, event_payload: dict, event_type: str, attempt: int) -> bool:
        """Schedule retry. Returns False if max retries exceeded."""
        if attempt > self._max_retries:
            return False
        if self._redis is None:
            return False
        backoff_idx = min(attempt - 1, len(self._backoffs) - 1)
        delay = self._backoffs[backoff_idx]
        next_time = time.time() + delay
        item = json.dumps(
            {
                "webhook_id": webhook_id,
                "event_payload": event_payload,
                "event_type": event_type,
                "attempt": attempt,
            },
            default=str,
        )
        await self._redis.zadd(self.RETRY_KEY, {item: next_time})
        logger.info("Scheduled retry %d for webhook %s in %ds", attempt, webhook_id, delay)
        return True

    async def get_due_retries(self) -> list[RetryItem]:
        """Fetch and remove all items whose scheduled time has passed."""
        if self._redis is None:
            return []
        now = time.time()
        items = await self._redis.zrangebyscore(self.RETRY_KEY, "-inf", now)
        if not items:
            return []
        pipe = self._redis.pipeline()
        for item in items:
            pipe.zrem(self.RETRY_KEY, item)
        await pipe.execute()
        result = []
        for raw in items:
            data = json.loads(raw)
            result.append(
                RetryItem(
                    webhook_id=data["webhook_id"],
                    event_payload=data["event_payload"],
                    event_type=data["event_type"],
                    attempt=data["attempt"],
                )
            )
        return result

    async def pending_count(self) -> int:
        if self._redis is None:
            return 0
        return await self._redis.zcard(self.RETRY_KEY)
