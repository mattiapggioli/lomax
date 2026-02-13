"""Tests for the Llomax orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from llomax.config import LlomaxConfig
from llomax.ia_client import SearchResult
from llomax.llomax import Llomax
from llomax.result import ImageResult, LlomaxResult


def _img(
    identifier: str,
    filename: str = "photo.jpg",
    fmt: str = "JPEG",
) -> ImageResult:
    """Build a minimal ImageResult for testing."""
    return ImageResult(
        identifier=identifier,
        filename=filename,
        download_url=(f"https://archive.org/download/{identifier}/{filename}"),
        format=fmt,
        size=1024,
        md5="abc123",
        metadata={"identifier": identifier, "title": "Test"},
    )


class TestLlomaxInit:
    """Tests for Llomax initialization."""

    def test_default_params(self) -> None:
        """Test Llomax initializes with default parameters."""
        lx = Llomax()
        assert lx.max_results == 10

    def test_custom_params(self) -> None:
        """Test Llomax initializes with custom parameters."""
        lx = Llomax(LlomaxConfig(max_results=5))
        assert lx.max_results == 5

    def test_stores_commercial_use(self) -> None:
        """Test Llomax stores commercial_use from config."""
        lx = Llomax(LlomaxConfig(commercial_use=True))
        assert lx.commercial_use is True

    def test_default_commercial_use(self) -> None:
        """Test Llomax defaults commercial_use to False."""
        lx = Llomax()
        assert lx.commercial_use is False


class TestLlomaxSearchPassthrough:
    """Tests that Llomax.search() forwards params to IAClient."""

    @patch("llomax.llomax.extract_keywords")
    def test_forwards_custom_params(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() passes stored params to IAClient."""
        mock_extract.return_value = ["test"]

        lx = Llomax(
            LlomaxConfig(
                max_results=3,
                commercial_use=True,
            )
        )
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult("t-1", "T1"),
        ]
        lx._client.get_item_images.return_value = [
            _img("t-1"),
        ]
        lx.search("test")

        lx._client.search.assert_called_once_with(
            ["test"],
            max_results=6,
            commercial_use=True,
        )


class TestLlomaxSearch:
    """Tests for Llomax.search() pipeline."""

    @patch("llomax.llomax.extract_keywords")
    def test_search_full_pipeline(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() scatter-gathers per keyword."""
        mock_extract.return_value = ["jazz", "photo"]

        sr_jazz = SearchResult(
            identifier="jazz-1",
            title="Jazz One",
            description="Desc",
            mediatype="image",
        )
        sr_photo = SearchResult(
            identifier="photo-1",
            title="Photo One",
            description="Desc",
            mediatype="image",
        )

        lx = Llomax(LlomaxConfig(max_results=2))
        lx._client = MagicMock()
        lx._client.search.side_effect = [
            [sr_jazz],
            [sr_photo],
        ]
        lx._client.get_item_images.side_effect = lambda id: {
            "jazz-1": [
                _img("jazz-1", "pic.jpg", "JPEG"),
            ],
            "photo-1": [
                _img("photo-1", "shot.png", "PNG"),
            ],
        }[id]
        result = lx.search("jazz, photo")

        mock_extract.assert_called_once_with("jazz, photo")
        assert lx._client.search.call_count == 2
        lx._client.search.assert_any_call(
            ["jazz"],
            max_results=4,
            commercial_use=False,
        )
        lx._client.search.assert_any_call(
            ["photo"],
            max_results=4,
            commercial_use=False,
        )
        assert isinstance(result, LlomaxResult)
        assert result.prompt == "jazz, photo"
        assert result.keywords == ["jazz", "photo"]
        assert result.total_items == 2
        ids = {img.identifier for img in result.images}
        assert "jazz-1" in ids
        assert "photo-1" in ids

    @patch("llomax.llomax.extract_keywords")
    def test_search_max_results_override(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test that max_results in search() overrides default."""
        mock_extract.return_value = ["test"]
        search_results = [SearchResult(f"id-{i}", f"T{i}") for i in range(10)]

        lx = Llomax(LlomaxConfig(max_results=10))
        lx._client = MagicMock()
        lx._client.search.return_value = search_results
        lx._client.get_item_images.side_effect = lambda id: [_img(id)]

        result = lx.search("test", max_results=3)
        assert result.total_items == 3

    @patch("llomax.llomax.extract_keywords")
    def test_search_empty_results(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() returns empty LlomaxResult when nothing."""
        mock_extract.return_value = ["nonexistent"]

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = []
        result = lx.search("nonexistent")

        assert isinstance(result, LlomaxResult)
        assert result.total_images == 0
        assert result.total_items == 0
        assert result.images == []

    def test_search_empty_prompt_raises(self) -> None:
        """Test search() propagates ValueError from keywords."""
        lx = Llomax()
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            lx.search("")

    @patch("llomax.llomax.extract_keywords")
    def test_search_skips_item_with_no_images(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() skips items that have no image files."""
        mock_extract.return_value = ["test"]

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="no-images", title="No Images")
        ]
        lx._client.get_item_images.return_value = []
        result = lx.search("test")

        assert result.total_images == 0

    @patch("llomax.llomax.extract_keywords")
    def test_search_skips_item_on_get_item_failure(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() skips items when get_item_images fails."""
        mock_extract.return_value = ["test"]

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="fail", title="Fail")
        ]
        lx._client.get_item_images.return_value = []
        result = lx.search("test")

        assert result.total_images == 0

    @patch("llomax.llomax.extract_keywords")
    def test_search_multiple_files_per_item(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() returns multiple ImageResults per item."""
        mock_extract.return_value = ["multi"]

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="multi", title="Multi")
        ]
        lx._client.get_item_images.return_value = [
            _img("multi", "a.jpg", "JPEG"),
            _img("multi", "b.png", "PNG"),
            _img("multi", "c.gif", "GIF"),
        ]
        result = lx.search("multi")

        assert result.total_images == 3
        assert result.total_items == 1
        filenames = {img.filename for img in result.images}
        assert filenames == {"a.jpg", "b.png", "c.gif"}

    @patch("llomax.llomax.extract_keywords")
    def test_search_includes_item_metadata(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test that ImageResult.metadata contains item fields."""
        mock_extract.return_value = ["jazz"]

        meta = {
            "identifier": "meta-test",
            "title": "Jazz Photo",
            "description": "A jazz photo",
            "creator": "John Doe",
            "date": "1955-03-12",
            "year": "1955",
            "subject": ["jazz", "photography"],
            "collection": ["jazz-collection"],
            "licenseurl": ("https://creativecommons.org/licenses/by/4.0/"),
            "rights": "Public Domain",
            "publisher": "Archive Press",
        }

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(
                identifier="meta-test",
                title="Jazz Photo",
            )
        ]
        lx._client.get_item_images.return_value = [
            ImageResult(
                identifier="meta-test",
                filename="pic.jpg",
                download_url=(
                    "https://archive.org/download/meta-test/pic.jpg"
                ),
                format="JPEG",
                size=1024,
                md5="abc123",
                metadata=meta,
            ),
        ]
        result = lx.search("jazz")

        m = result.images[0].metadata
        assert m["identifier"] == "meta-test"
        assert m["title"] == "Jazz Photo"
        assert m["description"] == "A jazz photo"
        assert m["creator"] == "John Doe"
        assert m["date"] == "1955-03-12"
        assert m["year"] == "1955"
        assert m["subject"] == ["jazz", "photography"]
        assert m["collection"] == ["jazz-collection"]
        assert m["rights"] == "Public Domain"
        assert m["publisher"] == "Archive Press"

    @patch("llomax.llomax.extract_keywords")
    def test_search_missing_metadata_fields_are_none(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test metadata fields default to None when absent."""
        mock_extract.return_value = ["test"]

        meta = {
            "identifier": "sparse",
            "title": "Sparse",
            "description": "No extras",
            "creator": None,
            "date": None,
            "year": None,
            "subject": None,
            "collection": None,
            "licenseurl": None,
            "rights": None,
            "publisher": None,
        }

        lx = Llomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="sparse", title="Sparse")
        ]
        lx._client.get_item_images.return_value = [
            ImageResult(
                identifier="sparse",
                filename="img.jpg",
                download_url=("https://archive.org/download/sparse/img.jpg"),
                format="JPEG",
                size=1024,
                md5="abc123",
                metadata=meta,
            ),
        ]
        result = lx.search("test")

        m = result.images[0].metadata
        assert m["creator"] is None
        assert m["date"] is None
        assert m["year"] is None
        assert m["subject"] is None
        assert m["collection"] is None
        assert m["licenseurl"] is None
        assert m["rights"] is None
        assert m["publisher"] is None


class TestRoundRobinSample:
    """Tests for the round-robin sampling algorithm."""

    def test_balances_two_keyword_lists(self) -> None:
        """Round-robin alternates items from each keyword list."""
        lx = Llomax(LlomaxConfig(max_results=4))
        cats = [SearchResult(f"cat-{i}", f"Cat {i}") for i in range(3)]
        dogs = [SearchResult(f"dog-{i}", f"Dog {i}") for i in range(3)]
        result = lx._round_robin_sample([cats, dogs], limit=lx.max_results)
        ids = [sr.identifier for sr in result]
        assert ids == [
            "cat-0",
            "dog-0",
            "cat-1",
            "dog-1",
        ]

    def test_deduplicates_by_identifier(self) -> None:
        """Duplicate identifiers across lists are skipped."""
        lx = Llomax(LlomaxConfig(max_results=4))
        list_a = [
            SearchResult("shared", "Shared"),
            SearchResult("a-1", "A1"),
        ]
        list_b = [
            SearchResult("shared", "Shared"),
            SearchResult("b-1", "B1"),
        ]
        result = lx._round_robin_sample([list_a, list_b], limit=lx.max_results)
        ids = [sr.identifier for sr in result]
        assert ids == ["shared", "a-1", "b-1"]

    def test_exhausted_list_skipped(self) -> None:
        """When one list runs out, items come from remaining."""
        lx = Llomax(LlomaxConfig(max_results=4))
        short = [SearchResult("s-0", "S0")]
        long = [SearchResult(f"l-{i}", f"L{i}") for i in range(5)]
        result = lx._round_robin_sample([short, long], limit=lx.max_results)
        assert len(result) == 4
        ids = [sr.identifier for sr in result]
        assert ids == ["s-0", "l-0", "l-1", "l-2"]

    def test_stops_at_max_results(self) -> None:
        """Sampling stops once max_results items are collected."""
        lx = Llomax(LlomaxConfig(max_results=2))
        big = [SearchResult(f"x-{i}", f"X{i}") for i in range(10)]
        result = lx._round_robin_sample([big], limit=lx.max_results)
        assert len(result) == 2

    def test_empty_candidates(self) -> None:
        """Empty candidate list returns empty result."""
        lx = Llomax(LlomaxConfig(max_results=5))
        result = lx._round_robin_sample([], limit=lx.max_results)
        assert result == []

    def test_all_lists_empty(self) -> None:
        """All-empty candidate lists return empty result."""
        lx = Llomax(LlomaxConfig(max_results=5))
        result = lx._round_robin_sample([[], []], limit=lx.max_results)
        assert result == []

    def test_all_duplicates_across_lists(self) -> None:
        """When all items are duplicates, only unique ones kept."""
        lx = Llomax(LlomaxConfig(max_results=5))
        list_a = [SearchResult("x", "X")]
        list_b = [SearchResult("x", "X")]
        result = lx._round_robin_sample([list_a, list_b], limit=lx.max_results)
        assert len(result) == 1
        assert result[0].identifier == "x"

    def test_three_keyword_lists(self) -> None:
        """Round-robin works across three keyword lists."""
        lx = Llomax(LlomaxConfig(max_results=6))
        a = [SearchResult(f"a-{i}", f"A{i}") for i in range(3)]
        b = [SearchResult(f"b-{i}", f"B{i}") for i in range(3)]
        c = [SearchResult(f"c-{i}", f"C{i}") for i in range(3)]
        result = lx._round_robin_sample([a, b, c], limit=lx.max_results)
        ids = [sr.identifier for sr in result]
        assert ids == [
            "a-0",
            "b-0",
            "c-0",
            "a-1",
            "b-1",
            "c-1",
        ]


class TestScatterGather:
    """Tests for scatter-gather search integration."""

    @patch("llomax.llomax.extract_keywords")
    def test_per_keyword_limit_is_double(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Each keyword search uses max_results * 2 as limit."""
        mock_extract.return_value = ["a", "b"]

        lx = Llomax(LlomaxConfig(max_results=5))
        lx._client = MagicMock()
        lx._client.search.return_value = []
        lx.search("a, b")

        assert lx._client.search.call_count == 2
        for call_args in lx._client.search.call_args_list:
            _, kwargs = call_args
            assert kwargs["max_results"] == 10
            assert kwargs["commercial_use"] is False

    @patch("llomax.llomax.extract_keywords")
    def test_single_keyword_searches_once(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Single keyword degenerates to one search call."""
        mock_extract.return_value = ["jazz"]

        lx = Llomax(LlomaxConfig(max_results=3))
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult("j-0", "J0"),
            SearchResult("j-1", "J1"),
        ]
        lx._client.get_item_images.side_effect = lambda id: [_img(id)]

        result = lx.search("jazz")

        lx._client.search.assert_called_once_with(
            ["jazz"],
            max_results=6,
            commercial_use=False,
        )
        assert result.total_items == 2


class TestLlomaxResultToDict:
    """Tests for LlomaxResult.to_dict() serialization."""

    def test_to_dict_structure(self) -> None:
        """Test to_dict() returns correct structure."""
        img = ImageResult(
            identifier="test-id",
            filename="photo.jpg",
            download_url=("https://archive.org/download/test-id/photo.jpg"),
            format="JPEG",
            size=1024,
            md5="abc123",
            metadata={"title": "Test"},
        )
        result = LlomaxResult(
            prompt="jazz",
            keywords=["jazz"],
            images=[img],
        )
        d = result.to_dict()

        assert d["prompt"] == "jazz"
        assert d["keywords"] == ["jazz"]
        assert d["total_items"] == 1
        assert d["total_images"] == 1
        assert len(d["images"]) == 1
        assert d["images"][0]["identifier"] == "test-id"
        assert d["images"][0]["filename"] == "photo.jpg"
        assert d["images"][0]["metadata"] == {"title": "Test"}

    def test_to_dict_empty_result(self) -> None:
        """Test to_dict() with no images."""
        result = LlomaxResult(
            prompt="nothing",
            keywords=["nothing"],
            images=[],
        )
        d = result.to_dict()

        assert d["total_items"] == 0
        assert d["total_images"] == 0
        assert d["images"] == []
