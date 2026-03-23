"""Unit tests for the RIR aggregate root."""

from uuid import uuid4

import pytest
from ipam.rir.domain.events import (
    RIRCreated,
    RIRDeleted,
    RIRUpdated,
)
from ipam.rir.domain.rir import RIR
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_rir(
    name: str = "ARIN",
    is_private: bool = False,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> RIR:
    return RIR.create(
        name=name,
        is_private=is_private,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestRIRCreate:
    def test_create_returns_rir_instance(self):
        rir = make_rir()
        assert isinstance(rir, RIR)

    def test_create_sets_name(self):
        rir = make_rir(name="RIPE NCC")
        assert rir.name == "RIPE NCC"

    def test_create_with_custom_fields_and_tags(self):
        tag_id = uuid4()
        rir = make_rir(custom_fields={"region": "NA"}, tags=[tag_id])
        assert rir.custom_fields == {"region": "NA"}
        assert rir.tags == [tag_id]

    def test_create_emits_rir_created_event(self):
        rir = make_rir()
        events = rir.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RIRCreated)

    def test_create_version_is_1(self):
        rir = make_rir()
        assert rir.version == 1

    def test_create_is_not_deleted(self):
        rir = make_rir()
        assert rir._deleted is False

    def test_create_sets_is_private(self):
        rir = make_rir(is_private=True)
        assert rir.is_private is True

    def test_create_event_has_correct_aggregate_id(self):
        rir = make_rir()
        events = rir.collect_uncommitted_events()
        assert events[0].aggregate_id == rir.id


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestRIRUpdate:
    def test_update_description(self):
        rir = make_rir(description="old")
        rir.collect_uncommitted_events()
        rir.update(description="new description")
        assert rir.description == "new description"

    def test_update_is_private(self):
        rir = make_rir(is_private=False)
        rir.collect_uncommitted_events()
        rir.update(is_private=True)
        assert rir.is_private is True

    def test_update_custom_fields(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.update(custom_fields={"region": "EU"})
        assert rir.custom_fields == {"region": "EU"}

    def test_update_tags(self):
        tag_id = uuid4()
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.update(tags=[tag_id])
        assert rir.tags == [tag_id]

    def test_update_produces_rir_updated_event(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.update(description="updated")
        events = rir.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RIRUpdated)

    def test_update_increments_version(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.update(description="v2")
        assert rir.version == 2

    def test_update_deleted_raises_error(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            rir.update(description="should fail")


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestRIRDelete:
    def test_delete_marks_as_deleted(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.delete()
        assert rir._deleted is True

    def test_delete_produces_rir_deleted_event(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.delete()
        events = rir.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], RIRDeleted)

    def test_delete_increments_version(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.delete()
        assert rir.version == 2

    def test_double_delete_raises_error(self):
        rir = make_rir()
        rir.collect_uncommitted_events()
        rir.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            rir.delete()


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestRIRLoadFromHistory:
    def test_load_from_history_restores_state(self):
        original = make_rir(name="APNIC", is_private=False, description="original")
        original.update(description="updated", is_private=True)
        original.delete()
        events = original.collect_uncommitted_events()

        restored = RIR()
        restored.load_from_history(events)

        assert restored.name == "APNIC"
        assert restored.description == "updated"
        assert restored.is_private is True
        assert restored._deleted is True
        assert restored.version == 3

    def test_load_from_history_does_not_add_uncommitted_events(self):
        rir = make_rir()
        events = rir.collect_uncommitted_events()

        restored = RIR()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestRIRSnapshot:
    def test_to_snapshot_returns_dict(self):
        rir = make_rir()
        snap = rir.to_snapshot()
        assert isinstance(snap, dict)

    def test_snapshot_keys(self):
        rir = make_rir()
        snap = rir.to_snapshot()
        expected_keys = {"name", "is_private", "description", "custom_fields", "tags", "deleted"}
        assert expected_keys == snap.keys()

    def test_snapshot_roundtrip_preserves_state(self):
        tag_id = uuid4()
        rir = make_rir(
            name="LACNIC",
            is_private=True,
            description="test",
            custom_fields={"region": "SA"},
            tags=[tag_id],
        )
        snap = rir.to_snapshot()
        restored = RIR.from_snapshot(rir.id, snap, rir.version)

        assert restored.name == "LACNIC"
        assert restored.is_private is True
        assert restored.description == "test"
        assert restored.custom_fields == {"region": "SA"}
        assert restored.tags == [tag_id]
        assert restored.id == rir.id
        assert restored.version == rir.version
        assert restored.collect_uncommitted_events() == []
