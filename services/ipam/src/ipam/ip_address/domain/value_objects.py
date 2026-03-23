from enum import StrEnum


class IPAddressStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
    DHCP = "dhcp"
    SLAAC = "slaac"
