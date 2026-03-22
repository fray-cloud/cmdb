"""Tests for journal entry schemas and model."""

from datetime import UTC, datetime
from uuid import uuid4

from event.infrastructure.models import JournalEntryModel
from event.interface.schemas import (
    CreateJournalEntryRequest,
    JournalEntryListResponse,
    JournalEntryResponse,
)


class TestCreateJournalEntryRequest:
    def test_valid_entry_types(self) -> None:
        for entry_type in ("info", "success", "warning", "danger"):
            req = CreateJournalEntryRequest(
                object_type="prefix",
                object_id=uuid4(),
                entry_type=entry_type,
                comment="Test note",
            )
            assert req.entry_type == entry_type

    def test_invalid_entry_type_rejected(self) -> None:
        import pytest

        with pytest.raises(Exception):  # noqa: B017
            CreateJournalEntryRequest(
                object_type="prefix",
                object_id=uuid4(),
                entry_type="invalid",
                comment="Test",
            )

    def test_fields(self) -> None:
        oid = uuid4()
        req = CreateJournalEntryRequest(
            object_type="vrf",
            object_id=oid,
            entry_type="warning",
            comment="Check this VRF config",
        )
        assert req.object_type == "vrf"
        assert req.object_id == oid
        assert req.comment == "Check this VRF config"


class TestJournalEntryResponse:
    def test_from_dict(self) -> None:
        now = datetime.now(UTC)
        uid = uuid4()
        tid = uuid4()
        resp = JournalEntryResponse(
            id=uuid4(),
            object_type="prefix",
            object_id=uuid4(),
            entry_type="info",
            comment="Allocated for DC-1",
            user_id=uid,
            tenant_id=tid,
            created_at=now,
        )
        assert resp.entry_type == "info"
        assert resp.user_id == uid
        assert resp.tenant_id == tid

    def test_nullable_user_and_tenant(self) -> None:
        resp = JournalEntryResponse(
            id=uuid4(),
            object_type="ip_address",
            object_id=uuid4(),
            entry_type="danger",
            comment="Conflicting assignment",
            user_id=None,
            tenant_id=None,
            created_at=datetime.now(UTC),
        )
        assert resp.user_id is None
        assert resp.tenant_id is None


class TestJournalEntryListResponse:
    def test_empty(self) -> None:
        resp = JournalEntryListResponse(items=[], total=0, offset=0, limit=50)
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        items = [
            JournalEntryResponse(
                id=uuid4(),
                object_type="prefix",
                object_id=uuid4(),
                entry_type="info",
                comment=f"Note {i}",
                user_id=uuid4(),
                tenant_id=uuid4(),
                created_at=datetime.now(UTC),
            )
            for i in range(3)
        ]
        resp = JournalEntryListResponse(items=items, total=3, offset=0, limit=50)
        assert len(resp.items) == 3
        assert resp.total == 3


class TestJournalEntryModel:
    def test_tablename(self) -> None:
        assert JournalEntryModel.__tablename__ == "journal_entries"

    def test_table_args_has_indexes(self) -> None:
        index_names = [idx.name for idx in JournalEntryModel.__table_args__ if hasattr(idx, "name")]
        assert "ix_journal_object" in index_names
        assert "ix_journal_tenant" in index_names
