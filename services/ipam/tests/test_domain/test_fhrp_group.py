"""Unit tests for the FHRPGroup aggregate root."""

from uuid import uuid4

import pytest
from ipam.fhrp_group import FHRPAuthType, FHRPGroup, FHRPGroupCreated, FHRPGroupDeleted, FHRPGroupUpdated, FHRPProtocol
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_fhrp_group(
    protocol: FHRPProtocol = FHRPProtocol.VRRP,
    group_id_value: int = 1,
    auth_type: FHRPAuthType = FHRPAuthType.PLAINTEXT,
    auth_key: str = "",
    name: str = "",
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> FHRPGroup:
    return FHRPGroup.create(
        protocol=protocol,
        group_id_value=group_id_value,
        auth_type=auth_type,
        auth_key=auth_key,
        name=name,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestFHRPGroupCreate:
    def test_create_returns_fhrp_group_instance(self):
        group = make_fhrp_group()
        assert isinstance(group, FHRPGroup)

    def test_create_sets_protocol(self):
        group = make_fhrp_group(protocol=FHRPProtocol.HSRP)
        assert group.protocol == FHRPProtocol.HSRP

    def test_create_sets_group_id_value(self):
        group = make_fhrp_group(group_id_value=42)
        assert group.group_id_value == 42

    def test_create_with_custom_fields_and_tags(self):
        tag_id = uuid4()
        group = make_fhrp_group(custom_fields={"env": "prod"}, tags=[tag_id])
        assert group.custom_fields == {"env": "prod"}
        assert group.tags == [tag_id]

    def test_create_emits_fhrp_group_created_event(self):
        group = make_fhrp_group()
        events = group.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], FHRPGroupCreated)

    def test_create_version_is_1(self):
        group = make_fhrp_group()
        assert group.version == 1

    def test_create_is_not_deleted(self):
        group = make_fhrp_group()
        assert group._deleted is False

    def test_create_sets_auth_type(self):
        group = make_fhrp_group(auth_type=FHRPAuthType.MD5, auth_key="secret")
        assert group.auth_type == FHRPAuthType.MD5
        assert group.auth_key == "secret"

    def test_create_event_has_correct_aggregate_id(self):
        group = make_fhrp_group()
        events = group.collect_uncommitted_events()
        assert events[0].aggregate_id == group.id


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestFHRPGroupUpdate:
    def test_update_name(self):
        group = make_fhrp_group(name="old")
        group.collect_uncommitted_events()
        group.update(name="new name")
        assert group.name == "new name"

    def test_update_auth_type_and_auth_key(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.update(auth_type="md5", auth_key="newsecret")
        assert group.auth_type == FHRPAuthType.MD5
        assert group.auth_key == "newsecret"

    def test_update_custom_fields(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.update(custom_fields={"priority": "high"})
        assert group.custom_fields == {"priority": "high"}

    def test_update_tags(self):
        tag_id = uuid4()
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.update(tags=[tag_id])
        assert group.tags == [tag_id]

    def test_update_produces_fhrp_group_updated_event(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.update(name="updated")
        events = group.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], FHRPGroupUpdated)

    def test_update_increments_version(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.update(name="v2")
        assert group.version == 2

    def test_update_deleted_raises_error(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            group.update(name="should fail")


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestFHRPGroupDelete:
    def test_delete_marks_as_deleted(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.delete()
        assert group._deleted is True

    def test_delete_produces_fhrp_group_deleted_event(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.delete()
        events = group.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], FHRPGroupDeleted)

    def test_delete_increments_version(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.delete()
        assert group.version == 2

    def test_double_delete_raises_error(self):
        group = make_fhrp_group()
        group.collect_uncommitted_events()
        group.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            group.delete()


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestFHRPGroupLoadFromHistory:
    def test_load_from_history_restores_state(self):
        original = make_fhrp_group(
            protocol=FHRPProtocol.HSRP,
            group_id_value=10,
            name="original",
            auth_type=FHRPAuthType.PLAINTEXT,
        )
        original.update(name="updated", auth_type="md5", auth_key="secret")
        original.delete()
        events = original.collect_uncommitted_events()

        restored = FHRPGroup()
        restored.load_from_history(events)

        assert restored.protocol == FHRPProtocol.HSRP
        assert restored.group_id_value == 10
        assert restored.name == "updated"
        assert restored.auth_type == FHRPAuthType.MD5
        assert restored.auth_key == "secret"
        assert restored._deleted is True
        assert restored.version == 3

    def test_load_from_history_does_not_add_uncommitted_events(self):
        group = make_fhrp_group()
        events = group.collect_uncommitted_events()

        restored = FHRPGroup()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestFHRPGroupSnapshot:
    def test_to_snapshot_returns_dict(self):
        group = make_fhrp_group()
        snap = group.to_snapshot()
        assert isinstance(snap, dict)

    def test_snapshot_keys(self):
        group = make_fhrp_group()
        snap = group.to_snapshot()
        expected_keys = {
            "protocol",
            "group_id_value",
            "auth_type",
            "auth_key",
            "name",
            "description",
            "custom_fields",
            "tags",
            "deleted",
        }
        assert expected_keys == snap.keys()

    def test_snapshot_roundtrip_preserves_state(self):
        tag_id = uuid4()
        group = make_fhrp_group(
            protocol=FHRPProtocol.GLBP,
            group_id_value=5,
            auth_type=FHRPAuthType.MD5,
            auth_key="mykey",
            name="test-group",
            description="test",
            custom_fields={"priority": "high"},
            tags=[tag_id],
        )
        snap = group.to_snapshot()
        restored = FHRPGroup.from_snapshot(group.id, snap, group.version)

        assert restored.protocol == FHRPProtocol.GLBP
        assert restored.group_id_value == 5
        assert restored.auth_type == FHRPAuthType.MD5
        assert restored.auth_key == "mykey"
        assert restored.name == "test-group"
        assert restored.description == "test"
        assert restored.custom_fields == {"priority": "high"}
        assert restored.tags == [tag_id]
        assert restored.id == group.id
        assert restored.version == group.version
        assert restored.collect_uncommitted_events() == []
