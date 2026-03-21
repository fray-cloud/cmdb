from abc import ABC, abstractmethod
from uuid import UUID

from webhook.domain.webhook import Webhook
from webhook.domain.webhook_log import WebhookEventLog


class WebhookRepository(ABC):
    @abstractmethod
    async def find_by_id(self, webhook_id: UUID) -> Webhook | None: ...

    @abstractmethod
    async def find_all(
        self, *, offset: int = 0, limit: int = 50, is_active: bool | None = None, tenant_id: UUID | None = None
    ) -> tuple[list[Webhook], int]: ...

    @abstractmethod
    async def find_active_for_tenant(self, tenant_id: UUID | None) -> list[Webhook]: ...

    @abstractmethod
    async def save(self, webhook: Webhook) -> None: ...

    @abstractmethod
    async def delete(self, webhook_id: UUID) -> None: ...


class WebhookLogRepository(ABC):
    @abstractmethod
    async def save(self, log: WebhookEventLog) -> None: ...

    @abstractmethod
    async def find_by_webhook(
        self, webhook_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[list[WebhookEventLog], int]: ...
