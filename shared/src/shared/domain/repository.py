from abc import ABC, abstractmethod
from uuid import UUID

from shared.domain.entity import Entity


class Repository[T: Entity](ABC):
    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None: ...
