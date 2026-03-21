from ipam.domain.ip_address import IPAddress
from ipam.domain.ip_range import IPRange
from ipam.domain.prefix import Prefix


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


class AvailablePrefixService:
    def find_available(
        self,
        parent: Prefix,
        child_prefixes: list[Prefix],
        desired_prefix_length: int,
    ) -> list[str]:
        if parent.network is None:
            return []
        parent_net = parent.network.ip_network
        used_nets = sorted(
            [cp.network.ip_network for cp in child_prefixes if cp.network],
            key=lambda n: n.network_address,
        )
        available = []
        candidates = list(parent_net.subnets(new_prefix=desired_prefix_length))
        for candidate in candidates:
            overlaps = False
            for used in used_nets:
                if candidate.overlaps(used):
                    overlaps = True
                    break
            if not overlaps:
                available.append(str(candidate))
        return available


class IPRangeUtilizationService:
    def calculate(self, ip_range: IPRange, used_addresses: list[IPAddress]) -> float:
        if ip_range.start_address is None or ip_range.end_address is None:
            return 0.0
        start = int(ip_range.start_address.ip_address)
        end = int(ip_range.end_address.ip_address)
        total = end - start + 1
        if total <= 0:
            return 0.0
        in_range = 0
        for addr in used_addresses:
            if addr.address:
                ip_int = int(addr.address.ip_address)
                if start <= ip_int <= end:
                    in_range += 1
        return min(in_range / total, 1.0)


class IPAvailabilityService:
    def find_available(
        self,
        prefix: Prefix,
        used_addresses: list[IPAddress],
        count: int = 1,
    ) -> list[str]:
        if prefix.network is None:
            return []
        net = prefix.network.ip_network
        used_set = set()
        for addr in used_addresses:
            if addr.address:
                used_set.add(addr.address.ip_address)
        available = []
        for host in net.hosts():
            if host not in used_set:
                available.append(str(host))
                if len(available) >= count:
                    break
        return available
