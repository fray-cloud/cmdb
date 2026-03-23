from uuid import UUID

from shared.cqrs.command import Command


class CreateASNCommand(Command):
    asn: int
    rir_id: UUID | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateASNCommand(Command):
    asn_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteASNCommand(Command):
    asn_id: UUID


class BulkCreateASNsCommand(Command):
    items: list[CreateASNCommand]


class BulkUpdateASNItem(Command):
    asn_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateASNsCommand(Command):
    items: list[BulkUpdateASNItem]


class BulkDeleteASNsCommand(Command):
    ids: list[UUID]
