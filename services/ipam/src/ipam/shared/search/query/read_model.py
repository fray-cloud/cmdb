"""Global search repository interface — abstract full-text search contract."""

from abc import ABC, abstractmethod


class GlobalSearchRepository(ABC):
    """Abstract repository for cross-entity full-text search operations."""

    @abstractmethod
    async def search(
        self,
        query: str,
        entity_types: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]: ...
