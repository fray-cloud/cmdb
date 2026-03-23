"""Abstract repository interface for the Prefix aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from ipam.prefix.domain.prefix import Prefix


class PrefixRepository(ABC):
    """Domain repository interface for persisting and retrieving Prefix aggregates."""

    @abstractmethod
    async def find_by_id(self, prefix_id: UUID) -> Prefix | None: ...

    @abstractmethod
    async def save(self, prefix: Prefix) -> None: ...

    @abstractmethod
    async def delete(self, prefix_id: UUID) -> None: ...

    @abstractmethod
    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[Prefix]: ...

    @abstractmethod
    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[Prefix], int]: ...
