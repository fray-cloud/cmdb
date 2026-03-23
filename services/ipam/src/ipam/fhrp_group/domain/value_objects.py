"""FHRP Group value objects — protocol and authentication type enumerations."""

from enum import StrEnum


class FHRPProtocol(StrEnum):
    """Supported first-hop redundancy protocols (VRRP, HSRP, GLBP, CARP, other)."""

    VRRP = "vrrp"
    HSRP = "hsrp"
    GLBP = "glbp"
    CARP = "carp"
    OTHER = "other"


class FHRPAuthType(StrEnum):
    """Authentication type for FHRP groups (plaintext or MD5)."""

    PLAINTEXT = "plaintext"
    MD5 = "md5"
