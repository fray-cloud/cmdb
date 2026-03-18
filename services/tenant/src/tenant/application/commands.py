from uuid import UUID

from shared.cqrs.command import Command


class CreateTenantCommand(Command):
    name: str
    slug: str
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str | None = None


class SuspendTenantCommand(Command):
    tenant_id: UUID


class UpdateTenantSettingsCommand(Command):
    tenant_id: UUID
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str | None = None


class DeleteTenantCommand(Command):
    tenant_id: UUID
