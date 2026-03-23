from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class VLANGroupReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_slug(self, slug: str) -> dict | None: ...
