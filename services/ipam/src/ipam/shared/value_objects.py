import ipaddress

from pydantic import field_validator
from shared.domain.value_object import ValueObject


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


class RouteDistinguisher(ValueObject):
    rd: str

    @field_validator("rd")
    @classmethod
    def validate_rd(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError(f"Route Distinguisher must be in format 'ASN:NN' or 'IP:NN', got '{v}'")
        return v
