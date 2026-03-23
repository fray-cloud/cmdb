from uuid import UUID

from shared.cqrs.command import Command


class CreateIPRangeCommand(Command):
    start_address: str
    end_address: str
    vrf_id: UUID | None = None
    status: str = "active"
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateIPRangeCommand(Command):
    range_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class ChangeIPRangeStatusCommand(Command):
    range_id: UUID
    status: str


class DeleteIPRangeCommand(Command):
    range_id: UUID


class BulkCreateIPRangesCommand(Command):
    items: list[CreateIPRangeCommand]


class BulkUpdateIPRangeItem(Command):
    range_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateIPRangesCommand(Command):
    items: list[BulkUpdateIPRangeItem]


class BulkDeleteIPRangesCommand(Command):
    ids: list[UUID]
