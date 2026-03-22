from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

from shared.domain.exceptions import ValidationError


class FieldType(StrEnum):
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    URL = "url"


class CustomFieldDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    choices: list[str] | None = None
    validation_regex: str | None = None
    description: str = ""


_TYPE_VALIDATORS: dict[FieldType, type] = {
    FieldType.TEXT: str,
    FieldType.INTEGER: int,
    FieldType.FLOAT: float,
    FieldType.BOOLEAN: bool,
    FieldType.DATE: str,
    FieldType.DATETIME: str,
    FieldType.SELECT: str,
    FieldType.MULTISELECT: list,
    FieldType.URL: str,
}


class CustomFieldValidator:
    @staticmethod
    def validate(definition: CustomFieldDefinition, value: Any) -> Any:
        if value is None:
            if definition.required:
                raise ValidationError(
                    f"Field '{definition.name}' is required",
                    details={"field": definition.name},
                )
            return definition.default

        expected_type = _TYPE_VALIDATORS.get(definition.field_type)
        if expected_type and not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{definition.name}' expected {definition.field_type}, got {type(value).__name__}",
                details={"field": definition.name, "expected": definition.field_type},
            )

        if definition.choices is not None:
            if definition.field_type == FieldType.MULTISELECT:
                invalid = [v for v in value if v not in definition.choices]
                if invalid:
                    raise ValidationError(
                        f"Field '{definition.name}' invalid choices: {invalid}",
                        details={"field": definition.name, "invalid": invalid},
                    )
            elif value not in definition.choices:
                raise ValidationError(
                    f"Field '{definition.name}' value '{value}' not in choices",
                    details={"field": definition.name, "value": value},
                )

        if definition.validation_regex is not None:
            import re

            if not re.match(definition.validation_regex, str(value)):
                raise ValidationError(
                    f"Field '{definition.name}' failed regex validation",
                    details={"field": definition.name, "pattern": definition.validation_regex},
                )

        return value

    @staticmethod
    def validate_all(
        definitions: list[CustomFieldDefinition],
        values: dict[str, Any],
    ) -> dict[str, Any]:
        defs_by_name = {d.name: d for d in definitions}
        result: dict[str, Any] = {}

        for name, definition in defs_by_name.items():
            value = values.get(name)
            result[name] = CustomFieldValidator.validate(definition, value)

        unknown = set(values) - set(defs_by_name)
        if unknown:
            raise ValidationError(
                f"Unknown custom fields: {unknown}",
                details={"unknown_fields": list(unknown)},
            )

        return result
