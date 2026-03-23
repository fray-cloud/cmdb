"""Unit tests for the ASN aggregate root."""

from uuid import uuid4

import pytest
from ipam.asn.domain.asn import ASN
from ipam.asn.domain.events import (
    ASNCreated,
    ASNDeleted,
    ASNUpdated,
)
from ipam.asn.domain.value_objects import ASNumber
from pydantic import ValidationError
from shared.domain.exceptions import BusinessRuleViolationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_asn(
    asn: int = 65001,
    rir_id=None,
    tenant_id=None,
    description: str = "",
    custom_fields: dict | None = None,
    tags: list | None = None,
) -> ASN:
    return ASN.create(
        asn=asn,
        rir_id=rir_id,
        tenant_id=tenant_id,
        description=description,
        custom_fields=custom_fields,
        tags=tags,
    )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestASNCreate:
    def test_create_returns_asn_instance(self):
        aggregate = make_asn()
        assert isinstance(aggregate, ASN)

    def test_create_sets_asn(self):
        aggregate = make_asn(asn=65000)
        assert isinstance(aggregate.asn, ASNumber)
        assert aggregate.asn.asn == 65000

    def test_create_with_rir_id(self):
        rir_id = uuid4()
        aggregate = make_asn(rir_id=rir_id)
        assert aggregate.rir_id == rir_id

    def test_create_with_custom_fields_and_tags(self):
        tag_id = uuid4()
        aggregate = make_asn(custom_fields={"provider": "aws"}, tags=[tag_id])
        assert aggregate.custom_fields == {"provider": "aws"}
        assert aggregate.tags == [tag_id]

    def test_create_emits_asn_created_event(self):
        aggregate = make_asn()
        events = aggregate.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ASNCreated)

    def test_create_version_is_1(self):
        aggregate = make_asn()
        assert aggregate.version == 1

    def test_create_is_not_deleted(self):
        aggregate = make_asn()
        assert aggregate._deleted is False

    def test_create_invalid_asn_raises_error(self):
        with pytest.raises((ValueError, ValidationError)):
            make_asn(asn=0)

    def test_create_asn_too_large_raises_error(self):
        with pytest.raises((ValueError, ValidationError)):
            make_asn(asn=4294967296)

    def test_create_event_has_correct_aggregate_id(self):
        aggregate = make_asn()
        events = aggregate.collect_uncommitted_events()
        assert events[0].aggregate_id == aggregate.id


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestASNUpdate:
    def test_update_description(self):
        aggregate = make_asn(description="old")
        aggregate.collect_uncommitted_events()
        aggregate.update(description="new description")
        assert aggregate.description == "new description"

    def test_update_custom_fields(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.update(custom_fields={"provider": "gcp"})
        assert aggregate.custom_fields == {"provider": "gcp"}

    def test_update_tags(self):
        tag_id = uuid4()
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.update(tags=[tag_id])
        assert aggregate.tags == [tag_id]

    def test_update_produces_asn_updated_event(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.update(description="updated")
        events = aggregate.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ASNUpdated)

    def test_update_increments_version(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.update(description="v2")
        assert aggregate.version == 2

    def test_update_deleted_raises_error(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.delete()
        with pytest.raises(BusinessRuleViolationError, match="deleted"):
            aggregate.update(description="should fail")


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestASNDelete:
    def test_delete_marks_as_deleted(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.delete()
        assert aggregate._deleted is True

    def test_delete_produces_asn_deleted_event(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.delete()
        events = aggregate.collect_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ASNDeleted)

    def test_delete_increments_version(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.delete()
        assert aggregate.version == 2

    def test_double_delete_raises_error(self):
        aggregate = make_asn()
        aggregate.collect_uncommitted_events()
        aggregate.delete()
        with pytest.raises(BusinessRuleViolationError, match="already deleted"):
            aggregate.delete()


# ---------------------------------------------------------------------------
# load_from_history()
# ---------------------------------------------------------------------------


class TestASNLoadFromHistory:
    def test_load_from_history_restores_state(self):
        rir_id = uuid4()
        original = make_asn(asn=65100, rir_id=rir_id, description="original")
        original.update(description="updated")
        original.delete()
        events = original.collect_uncommitted_events()

        restored = ASN()
        restored.load_from_history(events)

        assert restored.asn.asn == 65100
        assert restored.rir_id == rir_id
        assert restored.description == "updated"
        assert restored._deleted is True
        assert restored.version == 3

    def test_load_from_history_does_not_add_uncommitted_events(self):
        aggregate = make_asn()
        events = aggregate.collect_uncommitted_events()

        restored = ASN()
        restored.load_from_history(events)

        assert restored.collect_uncommitted_events() == []


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------


class TestASNSnapshot:
    def test_to_snapshot_returns_dict(self):
        aggregate = make_asn()
        snap = aggregate.to_snapshot()
        assert isinstance(snap, dict)

    def test_snapshot_keys(self):
        aggregate = make_asn()
        snap = aggregate.to_snapshot()
        expected_keys = {"asn", "rir_id", "tenant_id", "description", "custom_fields", "tags", "deleted"}
        assert expected_keys == snap.keys()

    def test_snapshot_roundtrip_preserves_state(self):
        tag_id = uuid4()
        rir_id = uuid4()
        tenant_id = uuid4()
        aggregate = make_asn(
            asn=65200,
            rir_id=rir_id,
            tenant_id=tenant_id,
            description="test",
            custom_fields={"provider": "aws"},
            tags=[tag_id],
        )
        snap = aggregate.to_snapshot()
        restored = ASN.from_snapshot(aggregate.id, snap, aggregate.version)

        assert restored.asn.asn == 65200
        assert restored.rir_id == rir_id
        assert restored.tenant_id == tenant_id
        assert restored.description == "test"
        assert restored.custom_fields == {"provider": "aws"}
        assert restored.tags == [tag_id]
        assert restored.id == aggregate.id
        assert restored.version == aggregate.version
        assert restored.collect_uncommitted_events() == []
