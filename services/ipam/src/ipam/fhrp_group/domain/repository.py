"""FHRP Group repository interface — abstract persistence contract."""

from abc import ABC, abstractmethod
from uuid import UUID

from ipam.fhrp_group.domain.fhrp_group import FHRPGroup


class FHRPGroupRepository(ABC):
    """Abstract repository defining persistence operations for FHRP Group aggregates."""

    @abstractmethod
    async def find_by_id(self, group_id: UUID) -> FHRPGroup | None: ...

    @abstractmethod
    async def save(self, group: FHRPGroup) -> None: ...

    @abstractmethod
    async def delete(self, group_id: UUID) -> None: ...
