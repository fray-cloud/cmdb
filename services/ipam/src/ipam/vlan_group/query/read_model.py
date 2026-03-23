"""Abstract read model repository for VLANGroup queries."""

from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class VLANGroupReadModelRepository(ReadModelRepository):
    """Read-side repository interface for querying denormalized VLAN group data."""

    @abstractmethod
    async def find_by_slug(self, slug: str) -> dict | None: ...
