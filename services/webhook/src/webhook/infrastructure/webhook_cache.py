import json
import logging
from uuid import UUID

import redis.asyncio as redis

from webhook.domain.webhook import Webhook

logger = logging.getLogger(__name__)


class WebhookCache:
    def __init__(self, redis_url: str, ttl: int = 30) -> None:
        self._redis_url = redis_url
        self._ttl = ttl
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = redis.from_url(self._redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    def _key(self, tenant_id: UUID | None) -> str:
        return f"webhooks:active:{tenant_id}" if tenant_id else "webhooks:active:_global"

    async def get_active_webhooks(self, tenant_id: UUID | None) -> list[Webhook] | None:
        if self._redis is None:
            return None
        raw = await self._redis.get(self._key(tenant_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return [Webhook(**item) for item in data]

    async def set_active_webhooks(self, tenant_id: UUID | None, webhooks: list[Webhook]) -> None:
        if self._redis is None:
            return
        data = json.dumps([w.model_dump(mode="json") for w in webhooks])
        await self._redis.set(self._key(tenant_id), data, ex=self._ttl)

    async def invalidate(self, tenant_id: UUID | None) -> None:
        if self._redis is None:
            return
        await self._redis.delete(self._key(tenant_id))
