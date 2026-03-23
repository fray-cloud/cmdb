from uuid import UUID

from shared.cqrs.command import Command


class CreateIPAddressCommand(Command):
    address: str
    vrf_id: UUID | None = None
    status: str = "active"
    dns_name: str = ""
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateIPAddressCommand(Command):
    ip_id: UUID
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeIPAddressStatusCommand(Command):
    ip_id: UUID
    status: str


class DeleteIPAddressCommand(Command):
    ip_id: UUID


class BulkCreateIPAddressesCommand(Command):
    items: list[CreateIPAddressCommand]


class BulkUpdateIPAddressItem(Command):
    ip_id: UUID
    dns_name: str | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPAddressesCommand(Command):
    items: list[BulkUpdateIPAddressItem]


class BulkDeleteIPAddressesCommand(Command):
    ids: list[UUID]
