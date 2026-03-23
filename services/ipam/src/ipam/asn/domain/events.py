"""ASN domain events — ASNCreated, ASNUpdated, ASNDeleted."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class ASNCreated(DomainEvent):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class ASNUpdated(DomainEvent):
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ASNDeleted(DomainEvent):
    pass
