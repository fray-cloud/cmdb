from enum import StrEnum


class FHRPProtocol(StrEnum):
    VRRP = "vrrp"
    HSRP = "hsrp"
    GLBP = "glbp"
    CARP = "carp"
    OTHER = "other"


class FHRPAuthType(StrEnum):
    PLAINTEXT = "plaintext"
    MD5 = "md5"
