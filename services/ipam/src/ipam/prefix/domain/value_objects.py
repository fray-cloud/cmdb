"""Value objects for the Prefix domain."""

import ipaddress
from enum import StrEnum

from pydantic import field_validator
from shared.domain.value_object import ValueObject


class PrefixStatus(StrEnum):
    """Lifecycle status of a prefix."""

    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
    CONTAINER = "container"


class PrefixNetwork(ValueObject):
    """Immutable value object wrapping a validated IPv4 or IPv6 network CIDR."""

    network: str

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        ipaddress.ip_network(v, strict=False)
        return str(ipaddress.ip_network(v, strict=False))

    @property
    def ip_network(self) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        return ipaddress.ip_network(self.network, strict=False)

    @property
    def version(self) -> int:
        return self.ip_network.version

    @property
    def num_addresses(self) -> int:
        return self.ip_network.num_addresses

    @property
    def prefix_length(self) -> int:
        return self.ip_network.prefixlen

    def contains(self, other: "PrefixNetwork") -> bool:
        return other.ip_network.subnet_of(self.ip_network)
