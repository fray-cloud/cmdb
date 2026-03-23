from ipam.ip_address.domain.ip_address import IPAddress
from ipam.prefix.domain.prefix import Prefix


class PrefixUtilizationService:
    def calculate(
        self,
        prefix: Prefix,
        child_prefixes: list[Prefix],
        ip_addresses: list[IPAddress],
    ) -> float:
        if prefix.network is None:
            return 0.0
        total = prefix.network.num_addresses
        if total == 0:
            return 0.0
        used = sum(cp.network.num_addresses for cp in child_prefixes if cp.network)
        used += len(ip_addresses)
        return min(used / total, 1.0)
