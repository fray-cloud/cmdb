"""Route Target command definitions — create, update, delete, and bulk operations."""

from uuid import UUID

from shared.cqrs.command import Command


class CreateRouteTargetCommand(Command):
    name: str
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateRouteTargetCommand(Command):
    route_target_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteRouteTargetCommand(Command):
    route_target_id: UUID


class BulkCreateRouteTargetsCommand(Command):
    items: list[CreateRouteTargetCommand]


class BulkUpdateRouteTargetItem(Command):
    route_target_id: UUID
    description: str | None = None
    tenant_id: UUID | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateRouteTargetsCommand(Command):
    items: list[BulkUpdateRouteTargetItem]


class BulkDeleteRouteTargetsCommand(Command):
    ids: list[UUID]
