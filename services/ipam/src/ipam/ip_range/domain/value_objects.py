"""Value objects for the IPRange domain."""

from enum import StrEnum


class IPRangeStatus(StrEnum):
    """Lifecycle status of an IP range."""

    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
