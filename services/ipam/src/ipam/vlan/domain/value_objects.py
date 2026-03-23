"""Value objects for the VLAN domain."""

from enum import StrEnum

from pydantic import field_validator
from shared.domain.value_object import ValueObject


class VLANStatus(StrEnum):
    """Lifecycle status of a VLAN."""

    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"


class VLANId(ValueObject):
    """Immutable value object wrapping a validated IEEE 802.1Q VLAN identifier (1-4094)."""

    vid: int

    @field_validator("vid")
    @classmethod
    def validate_vid(cls, v: int) -> int:
        if not 1 <= v <= 4094:
            raise ValueError(f"VLAN ID must be between 1 and 4094, got {v}")
        return v
