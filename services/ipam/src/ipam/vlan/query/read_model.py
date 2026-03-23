from abc import abstractmethod
from uuid import UUID

from ipam.shared.query_utils import ReadModelRepository


class VLANReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_vid(self, vid: int, group_id: UUID | None) -> dict | None: ...
