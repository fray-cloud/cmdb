from abc import ABC, abstractmethod
from uuid import UUID


class SavedFilterRepository(ABC):
    @abstractmethod
    async def find_by_id(self, filter_id: UUID) -> dict | None: ...

    @abstractmethod
    async def find_by_user(self, user_id: UUID, entity_type: str | None = None) -> list[dict]: ...

    @abstractmethod
    async def create(self, data: dict) -> UUID: ...

    @abstractmethod
    async def update(self, filter_id: UUID, data: dict) -> None: ...

    @abstractmethod
    async def delete(self, filter_id: UUID) -> None: ...

    @abstractmethod
    async def clear_default(self, user_id: UUID, entity_type: str) -> None: ...
