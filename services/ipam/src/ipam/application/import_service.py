"""CSV import service — parses CSV content into command-ready dicts."""

from __future__ import annotations

import csv
import io
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int
    field: str
    error: str


# Fields that should be parsed as UUID
_UUID_FIELDS = {"vrf_id", "vlan_id", "tenant_id", "rir_id", "group_id"}

# Fields that should be parsed as int
_INT_FIELDS = {"vid", "asn", "group_id_value", "min_vid", "max_vid"}

# Fields that should be parsed as bool
_BOOL_FIELDS = {"is_private"}

# Fields that should be parsed as JSON
_JSON_FIELDS = {"custom_fields", "tags", "import_targets", "export_targets", "ports", "ip_addresses"}


def _convert_value(field: str, value: str) -> Any:
    """Convert a CSV string value to the appropriate Python type."""
    stripped = value.strip()
    if stripped == "":
        return None

    if field in _UUID_FIELDS:
        return UUID(stripped)
    if field in _INT_FIELDS:
        return int(stripped)
    if field in _BOOL_FIELDS:
        return stripped.lower() in ("true", "1", "yes")
    if field in _JSON_FIELDS:
        return json.loads(stripped)
    return stripped


def parse_csv(content: str) -> tuple[list[dict[str, Any]], list[ImportRowError]]:
    """Parse CSV content into a list of dicts ready for BulkCreate commands.

    Returns:
        Tuple of (parsed_items, errors). Each parsed item is a dict with
        field names matching CreateCommand fields.
    """
    reader = csv.DictReader(io.StringIO(content))
    items: list[dict[str, Any]] = []
    errors: list[ImportRowError] = []

    for row_num, row in enumerate(reader, start=2):  # row 1 is header
        item: dict[str, Any] = {}
        row_has_error = False

        for field, raw_value in row.items():
            if field is None or raw_value is None:
                continue
            field = field.strip()
            if not field:
                continue
            try:
                converted = _convert_value(field, raw_value)
                if converted is not None:
                    item[field] = converted
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(ImportRowError(row=row_num, field=field, error=str(e)))
                row_has_error = True

        if not row_has_error and item:
            items.append(item)

    return items, errors


# Mapping from entity_type to BulkCreate command class name
ENTITY_COMMAND_MAP: dict[str, str] = {
    "prefix": "BulkCreatePrefixesCommand",
    "ip_address": "BulkCreateIPAddressesCommand",
    "vrf": "BulkCreateVRFsCommand",
    "vlan": "BulkCreateVLANsCommand",
    "ip_range": "BulkCreateIPRangesCommand",
    "rir": "BulkCreateRIRsCommand",
    "asn": "BulkCreateASNsCommand",
    "fhrp_group": "BulkCreateFHRPGroupsCommand",
    "route_target": "BulkCreateRouteTargetsCommand",
    "vlan_group": "BulkCreateVLANGroupsCommand",
    "service": "BulkCreateServicesCommand",
}

VALID_ENTITY_TYPES = set(ENTITY_COMMAND_MAP.keys())
