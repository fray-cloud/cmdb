"""Prefix utilization domain service — calculates address space usage within a prefix."""

from ipam.ip_address import IPAddress
from ipam.prefix import Prefix


class PrefixUtilizationService:
    """Calculates utilization ratio for a prefix based on child prefixes and IP addresses."""

    def calculate(
        self,
        prefix: Prefix,
        child_prefixes: list[Prefix],
        ip_addresses: list[IPAddress],
    ) -> float:
        """Calculate the utilization ratio (0.0 to 1.0) for the given prefix."""
        if prefix.network is None:
            return 0.0
        total = prefix.network.num_addresses
        if total == 0:
            return 0.0
        used = sum(cp.network.num_addresses for cp in child_prefixes if cp.network)
        used += len(ip_addresses)
        return min(used / total, 1.0)
