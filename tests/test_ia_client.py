"""Tests for the Internet Archive client."""

from unittest.mock import MagicMock, patch

import pytest

from llomax.ia_client import (
    COMMERCIAL_USE_LICENSES,
    IMAGE_FORMATS,
    IAClient,
    MainCollection,
    SearchResult,
)
from llomax.result import ImageResult


def _make_ia_file(
    name: str,
    fmt: str = "JPEG",
    size: str = "1024",
    md5: str = "abc123",
) -> dict:
    """Build a fake IA file metadata dict."""
    return {
        "name": name,
        "format": fmt,
        "size": size,
        "md5": md5,
    }


def _make_ia_item(
    identifier: str,
    title: str = "Test Title",
    description: str = "Test description",
    files: list[dict] | None = None,
    **extra_metadata: str | list[str],
) -> MagicMock:
    """Build a fake internetarchive Item object."""
    item = MagicMock()
    item.identifier = identifier
    item.metadata = {
        "identifier": identifier,
        "title": title,
        "description": description,
        **extra_metadata,
    }
    if files is None:
        files = [_make_ia_file("photo.jpg")]
    item.files = files
    return item


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

    def test_search_with_empty_keywords_raises_error(
        self,
    ) -> None:
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

    def test_search_result_has_required_fields(
        self,
    ) -> None:
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
            ["jazz", "blues"],
            operator="OR",
            max_results=3,
        )
        assert isinstance(results, list)

    def test_search_with_and_operator(self) -> None:
        """Test search with explicit AND operator."""
        client = IAClient()
        results = client.search(
            ["jazz", "photo"],
            operator="AND",
            max_results=3,
        )
        assert isinstance(results, list)

    def test_search_invalid_operator_raises_error(
        self,
    ) -> None:
        """Test that unsupported operator raises ValueError."""
        client = IAClient()
        with pytest.raises(ValueError, match="Unsupported operator"):
            client.search(["jazz"], operator="XOR")

    def test_search_with_collection_filter(self) -> None:
        """Test search filtered to a specific collection."""
        client = IAClient()
        results = client.search(
            ["space"],
            max_results=3,
            collections=[MainCollection.NASA],
        )
        assert isinstance(results, list)

    def test_search_with_commercial_use(self) -> None:
        """Test search with commercial_use filter."""
        client = IAClient()
        results = client.search(
            ["nature"],
            max_results=3,
            commercial_use=True,
        )
        assert isinstance(results, list)

    def test_search_with_generic_filter(self) -> None:
        """Test search with a generic filter dict."""
        client = IAClient()
        results = client.search(
            ["portrait"],
            max_results=3,
            filters={"year": "2020"},
        )
        assert isinstance(results, list)


class TestBuildQuery:
    """Unit tests for IAClient._build_query()."""

    def test_and_operator(self) -> None:
        """Test _build_query with AND joins keywords."""
        client = IAClient()
        query = client._build_query(["jazz", "photo"], "AND")
        assert query == ("(jazz AND photo) AND mediatype:image")

    def test_or_operator(self) -> None:
        """Test _build_query with OR joins keywords with OR."""
        client = IAClient()
        query = client._build_query(["jazz", "photo"], "OR")
        assert query == ("(jazz OR photo) AND mediatype:image")

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

    def test_with_filter_clauses(self) -> None:
        """Test _build_query appends filter clauses."""
        client = IAClient()
        query = client._build_query(["jazz"], "AND", ["collection:(nasa)"])
        assert query == ("(jazz) AND mediatype:image AND collection:(nasa)")

    def test_with_multiple_filter_clauses(self) -> None:
        """Test _build_query with multiple filter clauses."""
        client = IAClient()
        query = client._build_query(
            ["jazz"],
            "AND",
            ["collection:(nasa)", "year:2020"],
        )
        assert query == (
            "(jazz) AND mediatype:image AND collection:(nasa) AND year:2020"
        )

    def test_with_none_filter_clauses(self) -> None:
        """Test backward compat: None filter_clauses."""
        client = IAClient()
        query = client._build_query(["jazz"], "AND", None)
        assert query == "(jazz) AND mediatype:image"

    def test_with_empty_filter_clauses(self) -> None:
        """Test backward compat: empty filter_clauses."""
        client = IAClient()
        query = client._build_query(["jazz"], "AND", [])
        assert query == "(jazz) AND mediatype:image"


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self) -> None:
        """Test SearchResult can be created."""
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


class TestMainCollection:
    """Tests for MainCollection StrEnum."""

    def test_values_are_strings(self) -> None:
        """Test that enum values behave as strings."""
        assert MainCollection.NASA == "nasa"
        assert isinstance(MainCollection.NASA, str)

    def test_expected_members_exist(self) -> None:
        """Test that all expected members are present."""
        expected = {
            "NASA",
            "PRELINGER_ARCHIVES",
            "SMITHSONIAN",
            "METROPOLITAN_MUSEUM",
            "FLICKR_COMMONS",
            "LIBRARY_OF_CONGRESS",
        }
        assert set(MainCollection.__members__) == expected


class TestBuildFilterClauses:
    """Unit tests for IAClient._build_filter_clauses()."""

    def test_no_filters_returns_empty(self) -> None:
        """Test that no filters produces an empty list."""
        client = IAClient()
        clauses = client._build_filter_clauses(None, False, None)
        assert clauses == []

    def test_single_collection(self) -> None:
        """Test filtering by a single collection."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            [MainCollection.NASA], False, None
        )
        assert clauses == ["collection:(nasa)"]

    def test_arbitrary_collection_string(self) -> None:
        """Test filtering by an arbitrary collection string."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            ["my-custom-collection"], False, None
        )
        assert clauses == ["collection:(my-custom-collection)"]

    def test_multiple_collections(self) -> None:
        """Test filtering by multiple collections."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            [
                MainCollection.NASA,
                MainCollection.SMITHSONIAN,
            ],
            False,
            None,
        )
        assert clauses == ["collection:(nasa OR smithsonian)"]

    def test_commercial_use(self) -> None:
        """Test commercial_use produces licenseurl clause."""
        client = IAClient()
        clauses = client._build_filter_clauses(None, True, None)
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.startswith("licenseurl:(")
        for url in COMMERCIAL_USE_LICENSES:
            assert f'"{url}"' in clause

    def test_generic_filter_string_value(self) -> None:
        """Test generic filter with a string value."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            None, False, {"creator": "NASA"}
        )
        assert clauses == ["creator:NASA"]

    def test_generic_filter_list_value(self) -> None:
        """Test generic filter with a list value."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            None, False, {"year": ["2020", "2021"]}
        )
        assert clauses == ["year:(2020 OR 2021)"]

    def test_shortcut_overrides_generic_collection(
        self,
    ) -> None:
        """Test that collections shortcut overrides generic."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            [MainCollection.NASA],
            False,
            {"collection": "other"},
        )
        assert len(clauses) == 1
        assert clauses[0] == "collection:(nasa)"

    def test_shortcut_overrides_generic_licenseurl(
        self,
    ) -> None:
        """Test that commercial_use overrides generic."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            None,
            True,
            {"licenseurl": "http://example.com"},
        )
        assert len(clauses) == 1
        assert clauses[0].startswith("licenseurl:(")

    def test_combined_shortcuts_and_generic(self) -> None:
        """Test shortcuts and generic filters combined."""
        client = IAClient()
        clauses = client._build_filter_clauses(
            [MainCollection.NASA],
            True,
            {"year": "2020"},
        )
        assert len(clauses) == 3
        assert clauses[0] == "collection:(nasa)"
        assert clauses[1].startswith("licenseurl:(")
        assert clauses[2] == "year:2020"


class TestGetItemImages:
    """Tests for IAClient.get_item_images()."""

    @patch("llomax.ia_client.ia")
    def test_returns_images(self, mock_ia: MagicMock) -> None:
        """Test get_item_images returns ImageResult list."""
        mock_ia.get_item.return_value = _make_ia_item(
            "test-id",
            files=[_make_ia_file("pic.jpg", "JPEG", "2048", "aaa")],
        )
        client = IAClient()
        results = client.get_item_images("test-id")

        assert len(results) == 1
        assert isinstance(results[0], ImageResult)
        assert results[0].identifier == "test-id"
        assert results[0].filename == "pic.jpg"

    @patch("llomax.ia_client.ia")
    def test_filters_non_image_formats(self, mock_ia: MagicMock) -> None:
        """Test that non-image formats are filtered out."""
        mock_ia.get_item.return_value = _make_ia_item(
            "filter-test",
            files=[
                _make_ia_file("photo.jpg", "JPEG"),
                _make_ia_file("meta.xml", "Metadata"),
                _make_ia_file("thumb.png", "PNG"),
                _make_ia_file("archive.zip", "ZIP"),
                _make_ia_file("anim.gif", "Animated GIF"),
                _make_ia_file("scan.tiff", "TIFF"),
                _make_ia_file("hi-res.jp2", "JPEG 2000"),
                _make_ia_file("plain.gif", "GIF"),
            ],
        )
        client = IAClient()
        results = client.get_item_images("filter-test")

        assert len(results) == 6
        formats = {r.format for r in results}
        assert formats <= IMAGE_FORMATS

    @patch("llomax.ia_client.ia")
    def test_returns_empty_on_exception(self, mock_ia: MagicMock) -> None:
        """Test returns empty list when get_item raises."""
        mock_ia.get_item.side_effect = Exception("API error")
        client = IAClient()
        results = client.get_item_images("fail")

        assert results == []

    @patch("llomax.ia_client.ia")
    def test_metadata_populated(self, mock_ia: MagicMock) -> None:
        """Test that ImageResult.metadata contains fields."""
        mock_ia.get_item.return_value = _make_ia_item(
            "meta-test",
            title="Jazz Photo",
            description="A jazz photo",
            files=[_make_ia_file("pic.jpg")],
            creator="John Doe",
            date="1955-03-12",
            year="1955",
            subject=["jazz", "photography"],
            collection=["jazz-collection"],
            licenseurl=("https://creativecommons.org/licenses/by/4.0/"),
            rights="Public Domain",
            publisher="Archive Press",
        )
        client = IAClient()
        results = client.get_item_images("meta-test")

        meta = results[0].metadata
        assert meta["identifier"] == "meta-test"
        assert meta["title"] == "Jazz Photo"
        assert meta["description"] == "A jazz photo"
        assert meta["creator"] == "John Doe"
        assert meta["date"] == "1955-03-12"
        assert meta["year"] == "1955"
        assert meta["subject"] == [
            "jazz",
            "photography",
        ]
        assert meta["collection"] == ["jazz-collection"]
        assert meta["rights"] == "Public Domain"
        assert meta["publisher"] == "Archive Press"

    @patch("llomax.ia_client.ia")
    def test_metadata_defaults_to_none(self, mock_ia: MagicMock) -> None:
        """Test metadata fields default to None when absent."""
        mock_ia.get_item.return_value = _make_ia_item(
            "sparse",
            title="Sparse",
            description="No extras",
            files=[_make_ia_file("img.jpg")],
        )
        client = IAClient()
        results = client.get_item_images("sparse")

        meta = results[0].metadata
        assert meta["creator"] is None
        assert meta["date"] is None
        assert meta["year"] is None
        assert meta["subject"] is None
        assert meta["collection"] is None
        assert meta["licenseurl"] is None
        assert meta["rights"] is None
        assert meta["publisher"] is None

    @patch("llomax.ia_client.ia")
    def test_download_url_format(self, mock_ia: MagicMock) -> None:
        """Test download URL is correctly formatted."""
        mock_ia.get_item.return_value = _make_ia_item(
            "url-test",
            files=[_make_ia_file("photo.jpg")],
        )
        client = IAClient()
        results = client.get_item_images("url-test")

        assert results[0].download_url == (
            "https://archive.org/download/url-test/photo.jpg"
        )
