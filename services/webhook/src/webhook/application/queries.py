from uuid import UUID

from shared.cqrs.query import Query


class GetWebhookQuery(Query):
    webhook_id: UUID


class ListWebhooksQuery(Query):
    offset: int = 0
    limit: int = 50
    is_active: bool | None = None
    tenant_id: UUID | None = None


class ListWebhookLogsQuery(Query):
    webhook_id: UUID
    offset: int = 0
    limit: int = 50
