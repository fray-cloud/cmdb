from uuid import UUID

from shared.event.domain_event import DomainEvent


class VRFCreated(DomainEvent):
    name: str
    rd: str | None = None
    import_targets: list[UUID] = []
    export_targets: list[UUID] = []
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict = {}
    tags: list[UUID] = []


class VRFUpdated(DomainEvent):
    name: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class VRFDeleted(DomainEvent):
    pass
