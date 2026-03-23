"""API token repository interface for persistence abstraction."""

from abc import abstractmethod
from uuid import UUID

from shared.domain.repository import Repository

from auth.api_token.domain.api_token import APIToken


class APITokenRepository(Repository[APIToken]):
    """Abstract repository defining persistence operations for APIToken aggregates."""

    @abstractmethod
    async def find_by_key_hash(self, key_hash: str) -> APIToken | None: ...

    @abstractmethod
    async def find_all_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[APIToken], int]: ...
