"""ASN value objects — ASNumber with 32-bit range validation."""

from pydantic import field_validator
from shared.domain.value_object import ValueObject


class ASNumber(ValueObject):
    """Autonomous System Number value object (1 to 4294967295)."""

    asn: int

    @field_validator("asn")
    @classmethod
    def validate_asn(cls, v: int) -> int:
        if not 1 <= v <= 4294967295:
            raise ValueError(f"ASN must be between 1 and 4294967295, got {v}")
        return v
