"""Abstract read model repository for VRF queries."""

from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class VRFReadModelRepository(ReadModelRepository):
    """Read-side repository interface for querying denormalized VRF data."""

    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...
