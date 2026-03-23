"""IP range utilization domain service — calculates address usage within a range."""

from ipam.ip_address import IPAddress
from ipam.ip_range import IPRange


class IPRangeUtilizationService:
    """Calculates utilization ratio for an IP range based on assigned addresses."""

    def calculate(self, ip_range: IPRange, used_addresses: list[IPAddress]) -> float:
        """Calculate the utilization ratio (0.0 to 1.0) for the given IP range."""
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
