"""Saved filter command definitions — create, update, and delete commands."""

from uuid import UUID

from shared.cqrs.command import Command


class CreateSavedFilterCommand(Command):
    user_id: UUID
    name: str
    entity_type: str
    filter_config: dict = {}
    is_default: bool = False


class UpdateSavedFilterCommand(Command):
    filter_id: UUID
    name: str | None = None
    filter_config: dict | None = None
    is_default: bool | None = None


class DeleteSavedFilterCommand(Command):
    filter_id: UUID
