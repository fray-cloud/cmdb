from uuid import UUID

from shared.event.domain_event import DomainEvent


class ServiceCreated(DomainEvent):
    name: str
    protocol: str = "tcp"
    ports: list[int] = []
    ip_addresses: list[UUID] = []
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class ServiceUpdated(DomainEvent):
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ServiceDeleted(DomainEvent):
    pass
