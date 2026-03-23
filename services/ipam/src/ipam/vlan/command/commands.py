from uuid import UUID

from shared.cqrs.command import Command


class CreateVLANCommand(Command):
    vid: int
    name: str
    group_id: UUID | None = None
    status: str = "active"
    role: str | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateVLANCommand(Command):
    vlan_id: UUID
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeVLANStatusCommand(Command):
    vlan_id: UUID
    status: str


class DeleteVLANCommand(Command):
    vlan_id: UUID


class BulkCreateVLANsCommand(Command):
    items: list[CreateVLANCommand]


class BulkUpdateVLANItem(Command):
    vlan_id: UUID
    name: str | None = None
    role: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANsCommand(Command):
    items: list[BulkUpdateVLANItem]


class BulkDeleteVLANsCommand(Command):
    ids: list[UUID]
