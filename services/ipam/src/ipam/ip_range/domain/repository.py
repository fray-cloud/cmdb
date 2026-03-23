"""Abstract repository interface for the IPRange aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from ipam.ip_range.domain.ip_range import IPRange


class IPRangeRepository(ABC):
    """Domain repository interface for persisting and retrieving IPRange aggregates."""

    @abstractmethod
    async def find_by_id(self, range_id: UUID) -> IPRange | None: ...

    @abstractmethod
    async def save(self, ip_range: IPRange) -> None: ...

    @abstractmethod
    async def delete(self, range_id: UUID) -> None: ...
