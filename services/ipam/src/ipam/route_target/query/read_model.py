"""Route Target read model repository interface."""

from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class RouteTargetReadModelRepository(ReadModelRepository):
    """Abstract read model repository for Route Target queries."""

    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...
