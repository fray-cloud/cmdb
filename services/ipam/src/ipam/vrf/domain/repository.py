"""Abstract repository interface for the VRF aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from ipam.vrf.domain.vrf import VRF


class VRFRepository(ABC):
    """Domain repository interface for persisting and retrieving VRF aggregates."""

    @abstractmethod
    async def find_by_id(self, vrf_id: UUID) -> VRF | None: ...

    @abstractmethod
    async def save(self, vrf: VRF) -> None: ...

    @abstractmethod
    async def delete(self, vrf_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> VRF | None: ...
