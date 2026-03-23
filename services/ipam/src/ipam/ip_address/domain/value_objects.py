"""Value objects for the IPAddress domain."""

from enum import StrEnum


class IPAddressStatus(StrEnum):
    """Lifecycle status of an IP address."""

    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
    DHCP = "dhcp"
    SLAAC = "slaac"
