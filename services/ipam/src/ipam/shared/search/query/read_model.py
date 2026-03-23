from abc import ABC, abstractmethod


class GlobalSearchRepository(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        entity_types: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]: ...
