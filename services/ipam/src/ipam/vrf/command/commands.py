from uuid import UUID

from shared.cqrs.command import Command


class CreateVRFCommand(Command):
    name: str
    rd: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    tenant_id: UUID | None = None
    description: str = ""
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class UpdateVRFCommand(Command):
    vrf_id: UUID
    name: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class DeleteVRFCommand(Command):
    vrf_id: UUID


class BulkCreateVRFsCommand(Command):
    items: list[CreateVRFCommand]


class BulkUpdateVRFItem(Command):
    vrf_id: UUID
    name: str | None = None
    import_targets: list[UUID] | None = None
    export_targets: list[UUID] | None = None
    description: str | None = None
    custom_fields: dict | None = None
    tags: list[UUID] | None = None


class BulkUpdateVRFsCommand(Command):
    items: list[BulkUpdateVRFItem]


class BulkDeleteVRFsCommand(Command):
    ids: list[UUID]
