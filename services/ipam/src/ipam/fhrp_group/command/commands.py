"""FHRP Group command definitions — create, update, delete, and bulk operations."""

from uuid import UUID

from shared.cqrs.command import Command


class CreateFHRPGroupCommand(Command):
    protocol: str
    group_id_value: int
    auth_type: str = "plaintext"
    auth_key: str = ""
    name: str = ""
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateFHRPGroupCommand(Command):
    fhrp_group_id: UUID
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteFHRPGroupCommand(Command):
    fhrp_group_id: UUID


class BulkCreateFHRPGroupsCommand(Command):
    items: list[CreateFHRPGroupCommand]


class BulkUpdateFHRPGroupItem(Command):
    fhrp_group_id: UUID
    name: str | None = None
    auth_type: str | None = None
    auth_key: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateFHRPGroupsCommand(Command):
    items: list[BulkUpdateFHRPGroupItem]


class BulkDeleteFHRPGroupsCommand(Command):
    ids: list[UUID]
