"""Route Target domain events — RouteTargetCreated, RouteTargetUpdated, RouteTargetDeleted."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class RouteTargetCreated(DomainEvent):
    name: str
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class RouteTargetUpdated(DomainEvent):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RouteTargetDeleted(DomainEvent):
    pass
