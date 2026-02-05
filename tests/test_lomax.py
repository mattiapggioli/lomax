"""Tests for the Lomax orchestrator."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lomax.ia_client import SearchResult
from lomax.lomax import Lomax

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

    def test_default_params(self, tmp_path: Path) -> None:
        """Test Lomax initializes with default parameters."""
        lx = Lomax(output_dir=tmp_path / "output")
        assert lx.max_results == 10
        assert lx.output_dir == tmp_path / "output"

    def test_custom_params(self, tmp_path: Path) -> None:
        """Test Lomax initializes with custom parameters."""
        lx = Lomax(output_dir=tmp_path / "out", max_results=5)
        assert lx.max_results == 5


class TestLomaxRun:
    """Tests for Lomax.run() pipeline."""

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    @patch("lomax.lomax.extract_keywords")
    def test_run_full_pipeline(
        self,
        mock_extract: MagicMock,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run() wires keywords → search → download."""
        mock_extract.return_value = ["jazz", "photo"]

        sr = SearchResult(
            identifier="jazz-1",
            title="Jazz One",
            description="Desc",
            mediatype="image",
        )

        item = _make_ia_item(
            "jazz-1",
            files=[_make_ia_file("pic.jpg")],
        )
        mock_ia.get_item.return_value = item

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"\xff\xd8fake-jpeg"
        mock_get.return_value = mock_resp

        lx = Lomax(output_dir=tmp_path / "output", max_results=1)
        lx._client = MagicMock()
        lx._client.search.return_value = [sr]
        results = lx.run("jazz, photo")

        mock_extract.assert_called_once_with("jazz, photo")
        lx._client.search.assert_called_once_with(
            ["jazz", "photo"], max_results=1
        )
        assert len(results) == 1
        assert results[0].identifier == "jazz-1"

    @patch("lomax.lomax.extract_keywords")
    def test_run_empty_search_results(
        self,
        mock_extract: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test run() returns empty list when search finds nothing."""
        mock_extract.return_value = ["nonexistent"]

        lx = Lomax(output_dir=tmp_path / "output")
        lx._client = MagicMock()
        lx._client.search.return_value = []
        results = lx.run("nonexistent")
        assert results == []

    def test_run_empty_prompt_raises(self, tmp_path: Path) -> None:
        """Test run() propagates ValueError from extract_keywords."""
        lx = Lomax(output_dir=tmp_path / "output")
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            lx.run("")


class TestDownloadItem:
    """Tests for Lomax.download_item()."""

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_successful_download(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() downloads files and writes metadata."""
        item = _make_ia_item(
            "test-item",
            title="Test Title",
            description="Test description",
            files=[_make_ia_file("photo.jpg", "JPEG", "2048", "aaa")],
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

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"fake-image-bytes"
        mock_get.return_value = mock_resp

        sr = SearchResult(identifier="test-item", title="Test Title")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        assert result.identifier == "test-item"
        assert result.files_downloaded == 1
        assert result.directory == tmp_path / "output" / "test-item"
        assert result.metadata_path.exists()

        # Verify image file was written
        img_path = tmp_path / "output" / "test-item" / "photo.jpg"
        assert img_path.exists()
        assert img_path.read_bytes() == b"fake-image-bytes"

        # Verify metadata.json content
        meta = json.loads(result.metadata_path.read_text())
        assert meta["identifier"] == "test-item"
        assert meta["title"] == "Test Title"
        assert meta["description"] == "Test description"
        assert meta["creator"] == "John Doe"
        assert meta["date"] == "1955-03-12"
        assert meta["year"] == "1955"
        assert meta["subject"] == ["jazz", "photography"]
        assert meta["collection"] == ["jazz-collection"]
        assert meta["licenseurl"] == (
            "https://creativecommons.org/licenses/by/4.0/"
        )
        assert meta["rights"] == "Public Domain"
        assert meta["publisher"] == "Archive Press"
        assert len(meta["files"]) == 1
        assert meta["files"][0]["name"] == "photo.jpg"
        assert meta["files"][0]["format"] == "JPEG"
        assert meta["files"][0]["size"] == 2048
        assert meta["files"][0]["md5"] == "aaa"

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_metadata_contains_url(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test metadata file entries contain download URLs."""
        item = _make_ia_item(
            "url-test",
            files=[_make_ia_file("img.png", "PNG")],
        )
        mock_ia.get_item.return_value = item

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"png-bytes"
        mock_get.return_value = mock_resp

        sr = SearchResult(identifier="url-test", title="URL Test")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        meta = json.loads(result.metadata_path.read_text())
        expected_url = "https://archive.org/download/url-test/img.png"
        assert meta["files"][0]["url"] == expected_url

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_missing_metadata_fields_are_none(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test metadata fields default to None when absent."""
        item = _make_ia_item(
            "sparse-item",
            title="Sparse",
            description="No extras",
            files=[_make_ia_file("img.jpg")],
        )
        mock_ia.get_item.return_value = item

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"bytes"
        mock_get.return_value = mock_resp

        sr = SearchResult(identifier="sparse-item", title="Sparse")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        meta = json.loads(result.metadata_path.read_text())
        assert meta["creator"] is None
        assert meta["date"] is None
        assert meta["year"] is None
        assert meta["subject"] is None
        assert meta["collection"] is None
        assert meta["licenseurl"] is None
        assert meta["rights"] is None
        assert meta["publisher"] is None

    @patch("lomax.lomax.ia")
    def test_no_image_files(
        self,
        mock_ia: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() returns None when no image files."""
        item = _make_ia_item(
            "no-images",
            files=[_make_ia_file("data.xml", "Metadata")],
        )
        mock_ia.get_item.return_value = item

        sr = SearchResult(identifier="no-images", title="No Images")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is None

    @patch("lomax.lomax.ia")
    def test_get_item_failure(
        self,
        mock_ia: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() returns None when get_item fails."""
        mock_ia.get_item.side_effect = Exception("API error")

        sr = SearchResult(identifier="fail-item", title="Fail")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is None

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_partial_download_failure(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() skips failed files, keeps others."""
        item = _make_ia_item(
            "partial",
            files=[
                _make_ia_file("good.jpg", "JPEG"),
                _make_ia_file("bad.png", "PNG"),
            ],
        )
        mock_ia.get_item.return_value = item

        good_resp = MagicMock()
        good_resp.raise_for_status = MagicMock()
        good_resp.content = b"good-bytes"

        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = Exception("404")

        mock_get.side_effect = [good_resp, bad_resp]

        sr = SearchResult(identifier="partial", title="Partial")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        assert result.files_downloaded == 1

        meta = json.loads(result.metadata_path.read_text())
        assert len(meta["files"]) == 1
        assert meta["files"][0]["name"] == "good.jpg"

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_all_downloads_fail(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() returns None when all downloads fail."""
        item = _make_ia_item(
            "all-fail",
            files=[_make_ia_file("a.jpg", "JPEG")],
        )
        mock_ia.get_item.return_value = item

        mock_get.side_effect = Exception("Network error")

        sr = SearchResult(identifier="all-fail", title="All Fail")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is None

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_directory_creation(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() creates nested directories."""
        item = _make_ia_item("dir-test", files=[_make_ia_file("x.jpg")])
        mock_ia.get_item.return_value = item

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"bytes"
        mock_get.return_value = mock_resp

        out = tmp_path / "deep" / "nested" / "output"
        sr = SearchResult(identifier="dir-test", title="Dir Test")
        lx = Lomax(output_dir=out)
        result = lx.download_item(sr)

        assert result is not None
        assert result.directory.exists()
        assert result.directory == out / "dir-test"

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_multiple_files(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_item() handles multiple image files."""
        item = _make_ia_item(
            "multi",
            files=[
                _make_ia_file("a.jpg", "JPEG", "100", "m1"),
                _make_ia_file("b.png", "PNG", "200", "m2"),
                _make_ia_file("c.gif", "GIF", "300", "m3"),
            ],
        )
        mock_ia.get_item.return_value = item

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"img-data"
        mock_get.return_value = mock_resp

        sr = SearchResult(identifier="multi", title="Multi")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        assert result.files_downloaded == 3

        meta = json.loads(result.metadata_path.read_text())
        assert len(meta["files"]) == 3
        names = {f["name"] for f in meta["files"]}
        assert names == {"a.jpg", "b.png", "c.gif"}


class TestFormatFiltering:
    """Tests for image format filtering."""

    @patch("lomax.lomax.requests.get")
    @patch("lomax.lomax.ia")
    def test_only_image_formats_downloaded(
        self,
        mock_ia: MagicMock,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that non-image formats are filtered out."""
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

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"data"
        mock_get.return_value = mock_resp

        sr = SearchResult(identifier="filter-test", title="Filter Test")
        lx = Lomax(output_dir=tmp_path / "output")
        result = lx.download_item(sr)

        assert result is not None
        assert result.files_downloaded == 6

        meta = json.loads(result.metadata_path.read_text())
        formats = {f["format"] for f in meta["files"]}
        assert formats <= IMAGE_FORMATS
