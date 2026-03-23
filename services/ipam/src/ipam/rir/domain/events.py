from uuid import UUID

from shared.event.domain_event import DomainEvent


class RIRCreated(DomainEvent):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class RIRUpdated(DomainEvent):
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class RIRDeleted(DomainEvent):
    pass
