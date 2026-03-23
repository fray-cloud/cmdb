"""Tests for global search DTOs and queries."""

from uuid import uuid4

from ipam.shared.search.query import GlobalSearchQuery, GlobalSearchResultDTO, SearchResultDTO


class TestGlobalSearchQuery:
    def test_defaults(self) -> None:
        q = GlobalSearchQuery(q="test")
        assert q.q == "test"
        assert q.entity_types is None
        assert q.offset == 0
        assert q.limit == 20

    def test_with_entity_types(self) -> None:
        q = GlobalSearchQuery(q="prod", entity_types=["prefix", "vrf"], offset=10, limit=5)
        assert q.entity_types == ["prefix", "vrf"]
        assert q.offset == 10
        assert q.limit == 5


class TestSearchResultDTO:
    def test_from_dict(self) -> None:
        dto = SearchResultDTO(
            entity_type="prefix",
            entity_id=uuid4(),
            display_text="10.0.0.0/24",
            description="Management network",
            relevance=0.85,
        )
        assert dto.entity_type == "prefix"
        assert dto.display_text == "10.0.0.0/24"


class TestGlobalSearchResultDTO:
    def test_empty_results(self) -> None:
        result = GlobalSearchResultDTO(results=[], total=0)
        assert result.results == []
        assert result.total == 0

    def test_with_results(self) -> None:
        items = [
            SearchResultDTO(
                entity_type="prefix",
                entity_id=uuid4(),
                display_text="10.0.0.0/24",
                description="test",
                relevance=0.9,
            ),
            SearchResultDTO(
                entity_type="vrf",
                entity_id=uuid4(),
                display_text="production",
                description="prod vrf",
                relevance=0.7,
            ),
        ]
        result = GlobalSearchResultDTO(results=items, total=2)
        assert len(result.results) == 2
        assert result.total == 2
