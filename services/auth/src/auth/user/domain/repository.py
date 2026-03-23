"""User repository interface for persistence abstraction."""

from abc import abstractmethod
from uuid import UUID

from shared.domain.repository import Repository

from auth.user.domain.user import User


class UserRepository(Repository[User]):
    """Abstract repository defining persistence operations for User aggregates."""

    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: UUID) -> User | None: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]: ...
