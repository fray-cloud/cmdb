"""Tests for SavedFilter commands, queries, and DTOs."""

from datetime import UTC
from uuid import uuid4

from ipam.shared.saved_filter.command import (
    CreateSavedFilterCommand,
    DeleteSavedFilterCommand,
    UpdateSavedFilterCommand,
)
from ipam.shared.saved_filter.query import GetSavedFilterQuery, ListSavedFiltersQuery, SavedFilterDTO


class TestSavedFilterCommands:
    def test_create_command_defaults(self) -> None:
        cmd = CreateSavedFilterCommand(
            user_id=uuid4(),
            name="My Filter",
            entity_type="prefix",
        )
        assert cmd.filter_config == {}
        assert cmd.is_default is False

    def test_create_command_with_config(self) -> None:
        config = {"status": "active", "vrf_id": str(uuid4())}
        cmd = CreateSavedFilterCommand(
            user_id=uuid4(),
            name="Active Prefixes",
            entity_type="prefix",
            filter_config=config,
            is_default=True,
        )
        assert cmd.filter_config == config
        assert cmd.is_default is True

    def test_update_command_partial(self) -> None:
        cmd = UpdateSavedFilterCommand(filter_id=uuid4(), name="New Name")
        assert cmd.name == "New Name"
        assert cmd.filter_config is None
        assert cmd.is_default is None

    def test_delete_command(self) -> None:
        fid = uuid4()
        cmd = DeleteSavedFilterCommand(filter_id=fid)
        assert cmd.filter_id == fid


class TestSavedFilterQueries:
    def test_get_query(self) -> None:
        fid = uuid4()
        q = GetSavedFilterQuery(filter_id=fid)
        assert q.filter_id == fid

    def test_list_query_defaults(self) -> None:
        uid = uuid4()
        q = ListSavedFiltersQuery(user_id=uid)
        assert q.user_id == uid
        assert q.entity_type is None

    def test_list_query_with_entity_type(self) -> None:
        q = ListSavedFiltersQuery(user_id=uuid4(), entity_type="vrf")
        assert q.entity_type == "vrf"


class TestSavedFilterDTO:
    def test_dto_from_dict(self) -> None:
        from datetime import datetime

        now = datetime.now(UTC)
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "name": "Test Filter",
            "entity_type": "prefix",
            "filter_config": {"status": "active"},
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        }
        dto = SavedFilterDTO(**data)
        assert dto.name == "Test Filter"
        assert dto.filter_config == {"status": "active"}
