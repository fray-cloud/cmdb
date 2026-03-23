"""FHRP Group domain events — FHRPGroupCreated, FHRPGroupUpdated, FHRPGroupDeleted."""

from uuid import UUID

from shared.event.domain_event import DomainEvent


class FHRPGroupCreated(DomainEvent):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class FHRPGroupUpdated(DomainEvent):
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class FHRPGroupDeleted(DomainEvent):
    pass
