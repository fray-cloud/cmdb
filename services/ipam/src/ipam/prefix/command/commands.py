"""Command definitions for Prefix operations."""

from uuid import UUID

from shared.cqrs.command import Command


class CreatePrefixCommand(Command):
    network: str
    vrf_id: UUID | None = None
    vlan_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdatePrefixCommand(Command):
    prefix_id: UUID
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangePrefixStatusCommand(Command):
    prefix_id: UUID
    status: str


class DeletePrefixCommand(Command):
    prefix_id: UUID


class BulkCreatePrefixesCommand(Command):
    items: list[CreatePrefixCommand]


class BulkUpdatePrefixItem(Command):
    prefix_id: UUID
    description: str | None = None
    role: str | None = None
    tenant_id: UUID | None = None
    vlan_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdatePrefixesCommand(Command):
    items: list[BulkUpdatePrefixItem]


class BulkDeletePrefixesCommand(Command):
    ids: list[UUID]
