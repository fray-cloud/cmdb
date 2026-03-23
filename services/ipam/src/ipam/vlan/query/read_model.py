"""Abstract read model repository for VLAN queries."""

from abc import abstractmethod
from uuid import UUID

from ipam.shared.query_utils import ReadModelRepository


class VLANReadModelRepository(ReadModelRepository):
    """Read-side repository interface for querying denormalized VLAN data."""

    @abstractmethod
    async def find_by_vid(self, vid: int, group_id: UUID | None) -> dict | None: ...
