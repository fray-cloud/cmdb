"""Tests for common filter builder and query handler helpers."""

from datetime import UTC, datetime
from uuid import uuid4

from ipam.application.queries import BaseListQuery, ListPrefixesQuery
from ipam.application.query_handlers import _build_common_filters
from shared.api.filtering import FilterOperator


class TestBuildCommonFilters:
    def test_empty_query_returns_no_filters(self) -> None:
        query = BaseListQuery()
        filters, sort_params, tag_slugs, custom_field_filters = _build_common_filters(query)
        assert filters == []
        assert sort_params is None
        assert tag_slugs is None
        assert custom_field_filters is None

    def test_description_contains_produces_ilike_filter(self) -> None:
        query = BaseListQuery(description_contains="test")
        filters, _, _, _ = _build_common_filters(query)
        assert len(filters) == 1
        assert filters[0].field == "description"
        assert filters[0].operator == FilterOperator.ILIKE
        assert filters[0].value == "test"

    def test_created_after_produces_gte_filter(self) -> None:
        dt = datetime(2024, 1, 1, tzinfo=UTC)
        query = BaseListQuery(created_after=dt)
        filters, _, _, _ = _build_common_filters(query)
        assert len(filters) == 1
        assert filters[0].field == "created_at"
        assert filters[0].operator == FilterOperator.GTE

    def test_created_before_produces_lte_filter(self) -> None:
        dt = datetime(2024, 12, 31, tzinfo=UTC)
        query = BaseListQuery(created_before=dt)
        filters, _, _, _ = _build_common_filters(query)
        assert len(filters) == 1
        assert filters[0].field == "created_at"
        assert filters[0].operator == FilterOperator.LTE

    def test_updated_after_and_before(self) -> None:
        query = BaseListQuery(
            updated_after=datetime(2024, 1, 1, tzinfo=UTC),
            updated_before=datetime(2024, 12, 31, tzinfo=UTC),
        )
        filters, _, _, _ = _build_common_filters(query)
        assert len(filters) == 2
        fields = [f.field for f in filters]
        assert "updated_at" in fields

    def test_sort_by_produces_sort_params(self) -> None:
        query = BaseListQuery(sort_by="name", sort_dir="desc")
        _, sort_params, _, _ = _build_common_filters(query)
        assert sort_params is not None
        assert len(sort_params) == 1
        assert sort_params[0].field == "name"
        assert sort_params[0].direction == "desc"

    def test_tag_slugs_passed_through(self) -> None:
        query = BaseListQuery(tag_slugs=["production", "staging"])
        _, _, tag_slugs, _ = _build_common_filters(query)
        assert tag_slugs == ["production", "staging"]

    def test_custom_field_filters_passed_through(self) -> None:
        query = BaseListQuery(custom_field_filters={"env": "prod", "region": "kr"})
        _, _, _, custom_field_filters = _build_common_filters(query)
        assert custom_field_filters == {"env": "prod", "region": "kr"}

    def test_all_filters_combined(self) -> None:
        query = BaseListQuery(
            description_contains="network",
            created_after=datetime(2024, 1, 1, tzinfo=UTC),
            sort_by="created_at",
            tag_slugs=["prod"],
            custom_field_filters={"env": "prod"},
        )
        filters, sort_params, tag_slugs, cf = _build_common_filters(query)
        assert len(filters) == 2  # description + created_after
        assert sort_params is not None
        assert tag_slugs == ["prod"]
        assert cf == {"env": "prod"}


class TestListPrefixesQueryInheritance:
    def test_inherits_base_list_query_fields(self) -> None:
        query = ListPrefixesQuery(
            offset=10,
            limit=25,
            vrf_id=uuid4(),
            status="active",
            tenant_id=uuid4(),
            role="management",
            description_contains="test",
            sort_by="network",
        )
        assert query.offset == 10
        assert query.limit == 25
        assert query.role == "management"
        assert query.description_contains == "test"
        assert query.sort_by == "network"

    def test_defaults(self) -> None:
        query = ListPrefixesQuery()
        assert query.offset == 0
        assert query.limit == 50
        assert query.vrf_id is None
        assert query.status is None
        assert query.role is None
        assert query.tag_slugs is None
        assert query.sort_dir == "asc"
