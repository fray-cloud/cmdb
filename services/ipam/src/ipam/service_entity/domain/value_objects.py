"""Service value objects — transport protocol enumeration."""

from enum import StrEnum


class ServiceProtocol(StrEnum):
    """Transport protocol for network services (TCP, UDP, SCTP)."""

    TCP = "tcp"
    UDP = "udp"
    SCTP = "sctp"
