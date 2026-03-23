"""Permission value object and action enumeration for RBAC."""

from enum import StrEnum

from shared.domain.value_object import ValueObject


class Action(StrEnum):
    VIEW = "view"
    ADD = "add"
    CHANGE = "change"
    DELETE = "delete"


class Permission(ValueObject):
    """Immutable value object representing allowed actions on an object type."""

    object_type: str
    actions: list[str]
