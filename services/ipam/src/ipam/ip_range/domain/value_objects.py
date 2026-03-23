from enum import StrEnum


class IPRangeStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DEPRECATED = "deprecated"
