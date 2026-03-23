from __future__ import annotations

from uuid import UUID, uuid4

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.shared.saved_filter.query.read_model import SavedFilterRepository

# ---------------------------------------------------------------------------
# Saved Filter
# ---------------------------------------------------------------------------


class CreateSavedFilterHandler(CommandHandler[UUID]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> UUID:
        if command.is_default:
            await self._repo.clear_default(command.user_id, command.entity_type)
        return await self._repo.create(
            {
                "id": uuid4(),
                "user_id": command.user_id,
                "name": command.name,
                "entity_type": command.entity_type,
                "filter_config": command.filter_config,
                "is_default": command.is_default,
            }
        )


class UpdateSavedFilterHandler(CommandHandler[None]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> None:
        existing = await self._repo.find_by_id(command.filter_id)
        if existing is None:
            raise EntityNotFoundError(f"SavedFilter {command.filter_id} not found")
        update_data: dict = {}
        if command.name is not None:
            update_data["name"] = command.name
        if command.filter_config is not None:
            update_data["filter_config"] = command.filter_config
        if command.is_default is not None:
            update_data["is_default"] = command.is_default
            if command.is_default:
                await self._repo.clear_default(existing["user_id"], existing["entity_type"])
        if update_data:
            await self._repo.update(command.filter_id, update_data)


class DeleteSavedFilterHandler(CommandHandler[None]):
    def __init__(self, repo: SavedFilterRepository) -> None:
        self._repo = repo

    async def handle(self, command: Command) -> None:
        existing = await self._repo.find_by_id(command.filter_id)
        if existing is None:
            raise EntityNotFoundError(f"SavedFilter {command.filter_id} not found")
        await self._repo.delete(command.filter_id)
