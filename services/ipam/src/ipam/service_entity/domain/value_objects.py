from enum import StrEnum


class ServiceProtocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    SCTP = "sctp"
