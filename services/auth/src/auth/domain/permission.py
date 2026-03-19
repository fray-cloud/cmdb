from enum import StrEnum

from shared.domain.value_object import ValueObject


class Action(StrEnum):
    VIEW = "view"
    ADD = "add"
    CHANGE = "change"
    DELETE = "delete"


class Permission(ValueObject):
    object_type: str
    actions: list[str]
