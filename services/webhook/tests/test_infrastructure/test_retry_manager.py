import time

import fakeredis.aioredis
import pytest
import pytest_asyncio
from webhook.infrastructure.retry_manager import RetryManager


@pytest_asyncio.fixture
async def retry_manager():
    mgr = RetryManager("redis://localhost", max_retries=3, backoffs=[1, 2, 5])
    # Override Redis with fakeredis
    mgr._redis = fakeredis.aioredis.FakeRedis()
    yield mgr
    await mgr._redis.aclose()


class TestRetryManager:
    @pytest.mark.asyncio
    async def test_schedule_and_retrieve(self, retry_manager):
        scheduled = await retry_manager.schedule_retry("wh-1", {"test": True}, "ev.type", 1)
        assert scheduled is True
        # Set score to past to make it immediately due
        items = await retry_manager._redis.zrangebyscore(RetryManager.RETRY_KEY, "-inf", "+inf")
        assert len(items) == 1
        # Move the score to the past
        await retry_manager._redis.zadd(RetryManager.RETRY_KEY, {items[0]: time.time() - 10})
        due = await retry_manager.get_due_retries()
        assert len(due) == 1
        assert due[0].webhook_id == "wh-1"
        assert due[0].attempt == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, retry_manager):
        # max_retries=3, so attempt 4 should fail
        result = await retry_manager.schedule_retry("wh-1", {}, "ev", 4)
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_queue(self, retry_manager):
        due = await retry_manager.get_due_retries()
        assert due == []

    @pytest.mark.asyncio
    async def test_pending_count(self, retry_manager):
        await retry_manager.schedule_retry("wh-1", {}, "ev", 1)
        await retry_manager.schedule_retry("wh-2", {}, "ev", 2)
        count = await retry_manager.pending_count()
        assert count == 2
