import ipaddress
from enum import StrEnum

from pydantic import field_validator

from shared.domain.value_object import ValueObject


class PrefixStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
    CONTAINER = "container"


class IPAddressStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
    DHCP = "dhcp"
    SLAAC = "slaac"


class VLANStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"


class PrefixNetwork(ValueObject):
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


class IPAddressValue(ValueObject):
    address: str

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        ipaddress.ip_address(v)
        return str(ipaddress.ip_address(v))

    @property
    def ip_address(self) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        return ipaddress.ip_address(self.address)

    @property
    def version(self) -> int:
        return self.ip_address.version


class VLANId(ValueObject):
    vid: int

    @field_validator("vid")
    @classmethod
    def validate_vid(cls, v: int) -> int:
        if not 1 <= v <= 4094:
            raise ValueError(f"VLAN ID must be between 1 and 4094, got {v}")
        return v


class IPRangeStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"


class FHRPProtocol(StrEnum):
    VRRP = "vrrp"
    HSRP = "hsrp"
    GLBP = "glbp"
    CARP = "carp"
    OTHER = "other"


class FHRPAuthType(StrEnum):
    PLAINTEXT = "plaintext"
    MD5 = "md5"


class RouteDistinguisher(ValueObject):
    rd: str

    @field_validator("rd")
    @classmethod
    def validate_rd(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError(f"Route Distinguisher must be in format 'ASN:NN' or 'IP:NN', got '{v}'")
        return v


class ServiceProtocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    SCTP = "sctp"


class ASNumber(ValueObject):
    asn: int

    @field_validator("asn")
    @classmethod
    def validate_asn(cls, v: int) -> int:
        if not 1 <= v <= 4294967295:
            raise ValueError(f"ASN must be between 1 and 4294967295, got {v}")
        return v
