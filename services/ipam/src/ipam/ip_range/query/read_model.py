"""Abstract read model repository for IPRange queries."""

from ipam.shared.query_utils import ReadModelRepository


class IPRangeReadModelRepository(ReadModelRepository):
    """Read-side repository interface for querying denormalized IP range data."""

    pass
