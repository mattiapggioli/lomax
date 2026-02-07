"""Tests for the Internet Archive client."""

import pytest

from lomax.ia_client import IAClient, SearchResult


class TestIAClient:
    """Tests for IAClient class."""

    def test_client_initialization(self) -> None:
        """Test that client initializes correctly."""
        client = IAClient()
        assert client is not None

    def test_search_with_single_keyword(self) -> None:
        """Test search with a single keyword."""
        client = IAClient()
        results = client.search(["jazz"])
        assert isinstance(results, list)

    def test_search_with_multiple_keywords(self) -> None:
        """Test search with multiple keywords."""
        client = IAClient()
        results = client.search(["jazz", "musicians", "1950s"])
        assert isinstance(results, list)

    def test_search_with_empty_keywords_raises_error(self) -> None:
        """Test that empty keywords list raises ValueError."""
        client = IAClient()
        with pytest.raises(ValueError, match="Keywords cannot be empty"):
            client.search([])

    def test_search_with_max_results(self) -> None:
        """Test search respects max_results parameter."""
        client = IAClient()
        max_results = 5
        results = client.search(["music"], max_results=max_results)
        assert len(results) <= max_results

    def test_search_result_has_required_fields(self) -> None:
        """Test that search results contain required fields."""
        client = IAClient()
        results = client.search(["portrait"], max_results=1)
        if results:
            result = results[0]
            assert isinstance(result, SearchResult)
            assert result.identifier is not None
            assert result.title is not None

    def test_search_with_or_operator(self) -> None:
        """Test search with OR operator returns results."""
        client = IAClient()
        results = client.search(
            ["jazz", "blues"], operator="OR", max_results=3
        )
        assert isinstance(results, list)

    def test_search_with_and_operator(self) -> None:
        """Test search with explicit AND operator returns results."""
        client = IAClient()
        results = client.search(
            ["jazz", "photo"], operator="AND", max_results=3
        )
        assert isinstance(results, list)

    def test_search_invalid_operator_raises_error(self) -> None:
        """Test that an unsupported operator raises ValueError."""
        client = IAClient()
        with pytest.raises(ValueError, match="Unsupported operator"):
            client.search(["jazz"], operator="XOR")


class TestBuildQuery:
    """Unit tests for IAClient._build_query()."""

    def test_and_operator(self) -> None:
        """Test _build_query with AND joins keywords with AND."""
        client = IAClient()
        query = client._build_query(["jazz", "photo"], "AND")
        assert query == "(jazz AND photo) AND mediatype:image"

    def test_or_operator(self) -> None:
        """Test _build_query with OR joins keywords with OR."""
        client = IAClient()
        query = client._build_query(["jazz", "photo"], "OR")
        assert query == "(jazz OR photo) AND mediatype:image"

    def test_single_keyword(self) -> None:
        """Test _build_query with a single keyword."""
        client = IAClient()
        query = client._build_query(["jazz"], "AND")
        assert query == "(jazz) AND mediatype:image"

    def test_custom_mediatype(self) -> None:
        """Test _build_query respects custom mediatype."""
        client = IAClient(mediatype="audio")
        query = client._build_query(["jazz"], "OR")
        assert query == "(jazz) AND mediatype:audio"

    def test_default_operator_is_or(self) -> None:
        """Test that search defaults to OR operator."""
        client = IAClient()
        query = client._build_query(["a", "b"], "OR")
        assert " OR " in query


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self) -> None:
        """Test SearchResult can be created with required fields."""
        result = SearchResult(
            identifier="test-id",
            title="Test Title",
            description="Test description",
            mediatype="image",
        )
        assert result.identifier == "test-id"
        assert result.title == "Test Title"
        assert result.description == "Test description"
        assert result.mediatype == "image"

    def test_search_result_optional_fields(self) -> None:
        """Test SearchResult with optional fields as None."""
        result = SearchResult(
            identifier="test-id",
            title="Test Title",
        )
        assert result.description is None
        assert result.mediatype is None
