"""Tests for the Lomax orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from lomax.ia_client import SearchResult
from lomax.lomax import Lomax
from lomax.result import ImageResult, LomaxResult

IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "GIF",
    "TIFF",
    "JPEG 2000",
    "Animated GIF",
}


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


class TestLomaxInit:
    """Tests for Lomax initialization."""

    def test_default_params(self) -> None:
        """Test Lomax initializes with default parameters."""
        lx = Lomax()
        assert lx.max_results == 10

    def test_custom_params(self) -> None:
        """Test Lomax initializes with custom parameters."""
        lx = Lomax(max_results=5)
        assert lx.max_results == 5


class TestLomaxSearch:
    """Tests for Lomax.search() pipeline."""

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_full_pipeline(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
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

        item_jazz = _make_ia_item(
            "jazz-1",
            files=[_make_ia_file("pic.jpg", "JPEG", "2048", "aaa")],
        )
        item_photo = _make_ia_item(
            "photo-1",
            files=[_make_ia_file("shot.png", "PNG", "4096", "bbb")],
        )
        mock_ia.get_item.side_effect = lambda id: {
            "jazz-1": item_jazz,
            "photo-1": item_photo,
        }[id]

        lx = Lomax(max_results=2)
        lx._client = MagicMock()
        lx._client.search.side_effect = [[sr_jazz], [sr_photo]]
        result = lx.search("jazz, photo")

        mock_extract.assert_called_once_with("jazz, photo")
        assert lx._client.search.call_count == 2
        lx._client.search.assert_any_call(["jazz"], max_results=4)
        lx._client.search.assert_any_call(["photo"], max_results=4)
        assert isinstance(result, LomaxResult)
        assert result.prompt == "jazz, photo"
        assert result.keywords == ["jazz", "photo"]
        assert result.total_items == 2
        ids = {img.identifier for img in result.images}
        assert "jazz-1" in ids
        assert "photo-1" in ids

    @patch("lomax.lomax.extract_keywords")
    def test_search_empty_results(
        self,
        mock_extract: MagicMock,
    ) -> None:
        """Test search() returns empty LomaxResult when nothing found."""
        mock_extract.return_value = ["nonexistent"]

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = []
        result = lx.search("nonexistent")

        assert isinstance(result, LomaxResult)
        assert result.total_images == 0
        assert result.total_items == 0
        assert result.images == []

    def test_search_empty_prompt_raises(self) -> None:
        """Test search() propagates ValueError from extract_keywords."""
        lx = Lomax()
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            lx.search("")

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_skips_item_with_no_images(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test search() skips items that have no image files."""
        mock_extract.return_value = ["test"]

        item = _make_ia_item(
            "no-images",
            files=[_make_ia_file("data.xml", "Metadata")],
        )
        mock_ia.get_item.return_value = item

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="no-images", title="No Images")
        ]
        result = lx.search("test")

        assert result.total_images == 0

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_skips_item_on_get_item_failure(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test search() skips items when get_item raises."""
        mock_extract.return_value = ["test"]
        mock_ia.get_item.side_effect = Exception("API error")

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="fail", title="Fail")
        ]
        result = lx.search("test")

        assert result.total_images == 0

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_multiple_files_per_item(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test search() returns multiple ImageResults per item."""
        mock_extract.return_value = ["multi"]

        item = _make_ia_item(
            "multi",
            files=[
                _make_ia_file("a.jpg", "JPEG", "100", "m1"),
                _make_ia_file("b.png", "PNG", "200", "m2"),
                _make_ia_file("c.gif", "GIF", "300", "m3"),
            ],
        )
        mock_ia.get_item.return_value = item

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="multi", title="Multi")
        ]
        result = lx.search("multi")

        assert result.total_images == 3
        assert result.total_items == 1
        filenames = {img.filename for img in result.images}
        assert filenames == {"a.jpg", "b.png", "c.gif"}

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_filters_non_image_formats(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test that non-image formats are filtered out."""
        mock_extract.return_value = ["test"]

        item = _make_ia_item(
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
        mock_ia.get_item.return_value = item

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="filter-test", title="Filter")
        ]
        result = lx.search("test")

        assert result.total_images == 6
        formats = {img.format for img in result.images}
        assert formats <= IMAGE_FORMATS

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_includes_item_metadata(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test that ImageResult.metadata contains item-level fields."""
        mock_extract.return_value = ["jazz"]

        item = _make_ia_item(
            "meta-test",
            title="Jazz Photo",
            description="A jazz photo",
            files=[_make_ia_file("pic.jpg")],
            creator="John Doe",
            date="1955-03-12",
            year="1955",
            subject=["jazz", "photography"],
            collection=["jazz-collection"],
            licenseurl="https://creativecommons.org/licenses/by/4.0/",
            rights="Public Domain",
            publisher="Archive Press",
        )
        mock_ia.get_item.return_value = item

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="meta-test", title="Jazz Photo")
        ]
        result = lx.search("jazz")

        meta = result.images[0].metadata
        assert meta["identifier"] == "meta-test"
        assert meta["title"] == "Jazz Photo"
        assert meta["description"] == "A jazz photo"
        assert meta["creator"] == "John Doe"
        assert meta["date"] == "1955-03-12"
        assert meta["year"] == "1955"
        assert meta["subject"] == ["jazz", "photography"]
        assert meta["collection"] == ["jazz-collection"]
        assert meta["rights"] == "Public Domain"
        assert meta["publisher"] == "Archive Press"

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_search_missing_metadata_fields_are_none(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Test metadata fields default to None when absent."""
        mock_extract.return_value = ["test"]

        item = _make_ia_item(
            "sparse",
            title="Sparse",
            description="No extras",
            files=[_make_ia_file("img.jpg")],
        )
        mock_ia.get_item.return_value = item

        lx = Lomax()
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult(identifier="sparse", title="Sparse")
        ]
        result = lx.search("test")

        meta = result.images[0].metadata
        assert meta["creator"] is None
        assert meta["date"] is None
        assert meta["year"] is None
        assert meta["subject"] is None
        assert meta["collection"] is None
        assert meta["licenseurl"] is None
        assert meta["rights"] is None
        assert meta["publisher"] is None


class TestRoundRobinSample:
    """Tests for the round-robin sampling algorithm."""

    def test_balances_two_keyword_lists(self) -> None:
        """Round-robin alternates items from each keyword list."""
        lx = Lomax(max_results=4)
        cats = [SearchResult(f"cat-{i}", f"Cat {i}") for i in range(3)]
        dogs = [SearchResult(f"dog-{i}", f"Dog {i}") for i in range(3)]
        result = lx._round_robin_sample([cats, dogs])
        ids = [sr.identifier for sr in result]
        assert ids == ["cat-0", "dog-0", "cat-1", "dog-1"]

    def test_deduplicates_by_identifier(self) -> None:
        """Duplicate identifiers across lists are skipped."""
        lx = Lomax(max_results=4)
        list_a = [
            SearchResult("shared", "Shared"),
            SearchResult("a-1", "A1"),
        ]
        list_b = [
            SearchResult("shared", "Shared"),
            SearchResult("b-1", "B1"),
        ]
        result = lx._round_robin_sample([list_a, list_b])
        ids = [sr.identifier for sr in result]
        # "shared" taken from list_a, duplicate from list_b
        # dropped, then a-1 and b-1 interleaved
        assert ids == ["shared", "a-1", "b-1"]

    def test_exhausted_list_skipped(self) -> None:
        """When one list runs out, items come from remaining lists."""
        lx = Lomax(max_results=4)
        short = [SearchResult("s-0", "S0")]
        long = [SearchResult(f"l-{i}", f"L{i}") for i in range(5)]
        result = lx._round_robin_sample([short, long])
        assert len(result) == 4
        ids = [sr.identifier for sr in result]
        assert ids == ["s-0", "l-0", "l-1", "l-2"]

    def test_stops_at_max_results(self) -> None:
        """Sampling stops once max_results items are collected."""
        lx = Lomax(max_results=2)
        big = [SearchResult(f"x-{i}", f"X{i}") for i in range(10)]
        result = lx._round_robin_sample([big])
        assert len(result) == 2

    def test_empty_candidates(self) -> None:
        """Empty candidate list returns empty result."""
        lx = Lomax(max_results=5)
        result = lx._round_robin_sample([])
        assert result == []

    def test_all_lists_empty(self) -> None:
        """All-empty candidate lists return empty result."""
        lx = Lomax(max_results=5)
        result = lx._round_robin_sample([[], []])
        assert result == []

    def test_all_duplicates_across_lists(self) -> None:
        """When all items are duplicates, only unique ones kept."""
        lx = Lomax(max_results=5)
        list_a = [SearchResult("x", "X")]
        list_b = [SearchResult("x", "X")]
        result = lx._round_robin_sample([list_a, list_b])
        assert len(result) == 1
        assert result[0].identifier == "x"

    def test_three_keyword_lists(self) -> None:
        """Round-robin works across three keyword lists."""
        lx = Lomax(max_results=6)
        a = [SearchResult(f"a-{i}", f"A{i}") for i in range(3)]
        b = [SearchResult(f"b-{i}", f"B{i}") for i in range(3)]
        c = [SearchResult(f"c-{i}", f"C{i}") for i in range(3)]
        result = lx._round_robin_sample([a, b, c])
        ids = [sr.identifier for sr in result]
        assert ids == ["a-0", "b-0", "c-0", "a-1", "b-1", "c-1"]


class TestScatterGather:
    """Tests for scatter-gather search integration."""

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_per_keyword_limit_is_double(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Each keyword search uses max_results * 2 as limit."""
        mock_extract.return_value = ["a", "b"]

        lx = Lomax(max_results=5)
        lx._client = MagicMock()
        lx._client.search.return_value = []
        lx.search("a, b")

        assert lx._client.search.call_count == 2
        for call in lx._client.search.call_args_list:
            _, kwargs = call
            assert kwargs["max_results"] == 10

    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_single_keyword_searches_once(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
    ) -> None:
        """Single keyword degenerates to one search call."""
        mock_extract.return_value = ["jazz"]

        lx = Lomax(max_results=3)
        lx._client = MagicMock()
        lx._client.search.return_value = [
            SearchResult("j-0", "J0"),
            SearchResult("j-1", "J1"),
        ]
        mock_ia.get_item.side_effect = lambda id: _make_ia_item(
            id, files=[_make_ia_file(f"{id}.jpg")]
        )

        result = lx.search("jazz")

        lx._client.search.assert_called_once_with(["jazz"], max_results=6)
        assert result.total_items == 2


class TestLomaxResultToDict:
    """Tests for LomaxResult.to_dict() serialization."""

    def test_to_dict_structure(self) -> None:
        """Test to_dict() returns correct structure."""
        img = ImageResult(
            identifier="test-id",
            filename="photo.jpg",
            download_url="https://archive.org/download/test-id/photo.jpg",
            format="JPEG",
            size=1024,
            md5="abc123",
            metadata={"title": "Test"},
        )
        result = LomaxResult(
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
        result = LomaxResult(
            prompt="nothing",
            keywords=["nothing"],
            images=[],
        )
        d = result.to_dict()

        assert d["total_items"] == 0
        assert d["total_images"] == 0
        assert d["images"] == []
