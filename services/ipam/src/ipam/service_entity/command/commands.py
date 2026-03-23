"""Service command definitions — create, update, delete, and bulk operations."""

from uuid import UUID

from shared.cqrs.command import Command


class CreateServiceCommand(Command):
    name: str
    protocol: str = "tcp"
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateServiceCommand(Command):
    service_id: UUID
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteServiceCommand(Command):
    service_id: UUID


class BulkCreateServicesCommand(Command):
    items: list[CreateServiceCommand]


class BulkUpdateServiceItem(Command):
    service_id: UUID
    name: str | None = None
    protocol: str | None = None
    ports: list[int] | None = None
    ip_addresses: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateServicesCommand(Command):
    items: list[BulkUpdateServiceItem]


class BulkDeleteServicesCommand(Command):
    ids: list[UUID]
