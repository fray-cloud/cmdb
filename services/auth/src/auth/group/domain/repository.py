"""Group repository interface for persistence abstraction."""

from abc import abstractmethod
from uuid import UUID

from shared.domain.repository import Repository

from auth.group.domain.group import Group


class GroupRepository(Repository[Group]):
    """Abstract repository defining persistence operations for Group aggregates."""

    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Group | None: ...

    @abstractmethod
    async def find_by_ids(self, group_ids: list[UUID]) -> list[Group]: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Group], int]: ...
