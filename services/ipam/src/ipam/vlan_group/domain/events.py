"""Domain events emitted by the VLANGroup aggregate."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class VLANGroupCreated(DomainEvent):
    name: str
    slug: str
    min_vid: int = 1
    max_vid: int = 4094
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class VLANGroupUpdated(DomainEvent):
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VLANGroupDeleted(DomainEvent):
    pass
