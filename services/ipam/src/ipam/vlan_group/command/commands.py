from uuid import UUID

from shared.cqrs.command import Command


class CreateVLANGroupCommand(Command):
    name: str
    slug: str
    min_vid: int = 1
    max_vid: int = 4094
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateVLANGroupCommand(Command):
    vlan_group_id: UUID
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteVLANGroupCommand(Command):
    vlan_group_id: UUID


class BulkCreateVLANGroupsCommand(Command):
    items: list[CreateVLANGroupCommand]


class BulkUpdateVLANGroupItem(Command):
    vlan_group_id: UUID
    name: str | None = None
    description: str | None = None
    min_vid: int | None = None
    max_vid: int | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVLANGroupsCommand(Command):
    items: list[BulkUpdateVLANGroupItem]


class BulkDeleteVLANGroupsCommand(Command):
    ids: list[UUID]
