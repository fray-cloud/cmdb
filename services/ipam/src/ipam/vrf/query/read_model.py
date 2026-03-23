from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class VRFReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...
