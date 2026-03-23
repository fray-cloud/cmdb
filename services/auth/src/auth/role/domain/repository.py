"""Role repository interface for persistence abstraction."""

from abc import abstractmethod
from uuid import UUID

from shared.domain.repository import Repository

from auth.role.domain.role import Role


class RoleRepository(Repository[Role]):
    """Abstract repository defining persistence operations for Role aggregates."""

    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Role | None: ...

    @abstractmethod
    async def find_by_ids(self, role_ids: list[UUID]) -> list[Role]: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Role], int]: ...
