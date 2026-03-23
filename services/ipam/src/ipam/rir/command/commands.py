"""RIR command definitions — create, update, delete, and bulk operations."""

from uuid import UUID

from shared.cqrs.command import Command


class CreateRIRCommand(Command):
    name: str
    is_private: bool = False
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateRIRCommand(Command):
    rir_id: UUID
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteRIRCommand(Command):
    rir_id: UUID


class BulkCreateRIRsCommand(Command):
    items: list[CreateRIRCommand]


class BulkUpdateRIRItem(Command):
    rir_id: UUID
    description: str | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRIRsCommand(Command):
    items: list[BulkUpdateRIRItem]


class BulkDeleteRIRsCommand(Command):
    ids: list[UUID]
