"""Export service — converts DTO dicts to CSV, JSON, YAML formats."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any
from uuid import UUID

import yaml


def _serialize_value(value: Any) -> Any:
    """Convert non-serializable types to strings."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict | list):
        return json.dumps(value, default=str)
    return value


def _serialize_row(item: dict[str, Any]) -> dict[str, Any]:
    """Serialize a single row for export."""
    return {k: _serialize_value(v) for k, v in item.items()}


def export_csv(items: list[dict[str, Any]]) -> str:
    """Export items as CSV string."""
    if not items:
        return ""
    fields = list(items[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in items:
        writer.writerow(_serialize_row(item))
    return output.getvalue()


def export_json(items: list[dict[str, Any]]) -> str:
    """Export items as JSON string."""
    serialized = [_serialize_row(item) for item in items]
    return json.dumps(serialized, indent=2, ensure_ascii=False)


def export_yaml(items: list[dict[str, Any]]) -> str:
    """Export items as YAML string."""
    serialized = [_serialize_row(item) for item in items]
    return yaml.dump(serialized, allow_unicode=True, default_flow_style=False, sort_keys=False)
