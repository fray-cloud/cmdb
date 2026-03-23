from ipam.prefix.domain.prefix import Prefix


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
