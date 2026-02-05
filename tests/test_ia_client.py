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
