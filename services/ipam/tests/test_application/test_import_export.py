"""Tests for import/export services."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from ipam.shared.import_export import VALID_ENTITY_TYPES, export_csv, export_json, export_yaml, parse_csv


class TestParseCSV:
    def test_basic_prefix_csv(self) -> None:
        csv_content = "network,status,description\n10.0.0.0/24,active,Test network\n192.168.1.0/24,reserved,Lab\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 2
        assert len(errors) == 0
        assert items[0]["network"] == "10.0.0.0/24"
        assert items[0]["status"] == "active"
        assert items[1]["description"] == "Lab"

    def test_uuid_field_conversion(self) -> None:
        uid = str(uuid4())
        csv_content = f"network,vrf_id\n10.0.0.0/24,{uid}\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 1
        assert str(items[0]["vrf_id"]) == uid

    def test_int_field_conversion(self) -> None:
        csv_content = "vid,name\n100,VLAN100\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 1
        assert items[0]["vid"] == 100

    def test_bool_field_conversion(self) -> None:
        csv_content = "name,is_private\nRIPE,true\nARIN,false\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 2
        assert items[0]["is_private"] is True
        assert items[1]["is_private"] is False

    def test_json_field_conversion(self) -> None:
        import csv as csv_mod
        import io

        tag_id = str(uuid4())
        rows = [
            {"network": "10.0.0.0/24", "custom_fields": '{"env": "prod"}', "tags": f'["{tag_id}"]'},
        ]
        output = io.StringIO()
        writer = csv_mod.DictWriter(output, fieldnames=["network", "custom_fields", "tags"])
        writer.writeheader()
        writer.writerows(rows)
        csv_content = output.getvalue()

        items, errors = parse_csv(csv_content)
        assert len(errors) == 0
        assert len(items) == 1
        assert items[0]["custom_fields"] == {"env": "prod"}
        assert isinstance(items[0]["tags"], list)

    def test_empty_values_skipped(self) -> None:
        csv_content = "network,vrf_id,description\n10.0.0.0/24,,\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 1
        assert "vrf_id" not in items[0]
        assert "description" not in items[0]

    def test_invalid_uuid_produces_error(self) -> None:
        csv_content = "network,vrf_id\n10.0.0.0/24,not-a-uuid\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 0
        assert len(errors) == 1
        assert errors[0].row == 2
        assert errors[0].field == "vrf_id"

    def test_invalid_int_produces_error(self) -> None:
        csv_content = "vid,name\nabc,VLAN\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 0
        assert len(errors) == 1
        assert errors[0].field == "vid"

    def test_empty_csv(self) -> None:
        csv_content = "network,status\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 0
        assert len(errors) == 0

    def test_partial_errors(self) -> None:
        csv_content = "network,vrf_id\n10.0.0.0/24,\n192.168.0.0/16,bad-uuid\n172.16.0.0/12,\n"
        items, errors = parse_csv(csv_content)
        assert len(items) == 2  # rows 1 and 3 succeed
        assert len(errors) == 1  # row 2 fails


class TestValidEntityTypes:
    def test_all_entity_types(self) -> None:
        expected = {
            "prefix",
            "ip_address",
            "vrf",
            "vlan",
            "ip_range",
            "rir",
            "asn",
            "fhrp_group",
            "route_target",
            "vlan_group",
            "service",
        }
        assert expected == VALID_ENTITY_TYPES


class TestExportCSV:
    def test_basic_export(self) -> None:
        items = [
            {"network": "10.0.0.0/24", "status": "active"},
            {"network": "192.168.0.0/16", "status": "reserved"},
        ]
        result = export_csv(items)
        lines = result.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "network" in lines[0]
        assert "10.0.0.0/24" in lines[1]

    def test_empty_export(self) -> None:
        assert export_csv([]) == ""

    def test_uuid_serialization(self) -> None:
        uid = uuid4()
        items = [{"id": uid, "name": "test"}]
        result = export_csv(items)
        assert str(uid) in result

    def test_datetime_serialization(self) -> None:
        now = datetime.now(UTC)
        items = [{"name": "test", "created_at": now}]
        result = export_csv(items)
        assert now.isoformat() in result

    def test_dict_serialization(self) -> None:
        items = [{"name": "test", "custom_fields": {"env": "prod"}}]
        result = export_csv(items)
        assert '"env"' in result


class TestExportJSON:
    def test_basic_export(self) -> None:
        items = [{"network": "10.0.0.0/24", "status": "active"}]
        result = export_json(items)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["network"] == "10.0.0.0/24"

    def test_uuid_serialization(self) -> None:
        uid = uuid4()
        items = [{"id": uid}]
        result = export_json(items)
        parsed = json.loads(result)
        assert parsed[0]["id"] == str(uid)


class TestExportYAML:
    def test_basic_export(self) -> None:
        items = [{"network": "10.0.0.0/24", "status": "active"}]
        result = export_yaml(items)
        assert "network:" in result or "network: " in result
        assert "10.0.0.0/24" in result

    def test_uuid_serialization(self) -> None:
        uid = uuid4()
        items = [{"id": uid}]
        result = export_yaml(items)
        assert str(uid) in result
