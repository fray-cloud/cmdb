from ipam.ip_address.domain.ip_address import IPAddress
from ipam.prefix.domain.prefix import Prefix


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
