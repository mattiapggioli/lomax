"""Tests for the download utility."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from lomax.result import ImageResult, LomaxResult
from lomax.util import download_images


def _make_image(
    identifier: str = "test-item",
    filename: str = "photo.jpg",
    fmt: str = "JPEG",
    size: int = 1024,
    md5: str = "abc123",
    metadata: dict | None = None,
) -> ImageResult:
    """Build an ImageResult for testing."""
    if metadata is None:
        metadata = {
            "identifier": identifier,
            "title": "Test Title",
            "description": "Test description",
        }
    return ImageResult(
        identifier=identifier,
        filename=filename,
        download_url=(f"https://archive.org/download/{identifier}/{filename}"),
        format=fmt,
        size=size,
        md5=md5,
        metadata=metadata,
    )


def _make_result(
    images: list[ImageResult] | None = None,
) -> LomaxResult:
    """Build a LomaxResult for testing."""
    if images is None:
        images = [_make_image()]
    return LomaxResult(
        prompt="test",
        keywords=["test"],
        images=images,
    )


class TestDownloadImages:
    """Tests for download_images()."""

    @patch("lomax.util.requests.get")
    def test_successful_download(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() downloads files and writes metadata."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"fake-image-bytes"
        mock_get.return_value = mock_resp

        metadata = {
            "identifier": "test-item",
            "title": "Test Title",
            "description": "Test description",
            "creator": "John Doe",
            "date": "1955-03-12",
        }
        result = _make_result(
            images=[
                _make_image(metadata=metadata),
            ]
        )
        paths = download_images(result, tmp_path / "output")

        assert len(paths) == 1
        assert paths[0] == tmp_path / "output" / "test-item" / "photo.jpg"
        assert paths[0].exists()
        assert paths[0].read_bytes() == b"fake-image-bytes"

        # Verify metadata.json
        meta_path = tmp_path / "output" / "test-item" / "metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert meta["identifier"] == "test-item"
        assert meta["title"] == "Test Title"
        assert meta["creator"] == "John Doe"
        assert len(meta["files"]) == 1
        assert meta["files"][0]["name"] == "photo.jpg"
        assert meta["files"][0]["format"] == "JPEG"
        assert meta["files"][0]["size"] == 1024
        assert meta["files"][0]["md5"] == "abc123"

    @patch("lomax.util.requests.get")
    def test_metadata_contains_download_url(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test metadata file entries contain download URLs."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"bytes"
        mock_get.return_value = mock_resp

        result = _make_result(
            images=[_make_image(identifier="url-test", filename="img.png")]
        )
        paths = download_images(result, tmp_path / "output")

        assert len(paths) == 1
        meta_path = tmp_path / "output" / "url-test" / "metadata.json"
        meta = json.loads(meta_path.read_text())
        expected_url = "https://archive.org/download/url-test/img.png"
        assert meta["files"][0]["url"] == expected_url

    @patch("lomax.util.requests.get")
    def test_directory_creation(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() creates nested directories."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"bytes"
        mock_get.return_value = mock_resp

        out = tmp_path / "deep" / "nested" / "output"
        result = _make_result(images=[_make_image(identifier="dir-test")])
        paths = download_images(result, out)

        assert len(paths) == 1
        assert paths[0].parent == out / "dir-test"
        assert paths[0].parent.exists()

    @patch("lomax.util.requests.get")
    def test_multiple_files_per_item(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() handles multiple files per item."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.content = b"img-data"
        mock_get.return_value = mock_resp

        metadata = {"identifier": "multi", "title": "Multi"}
        result = _make_result(
            images=[
                _make_image("multi", "a.jpg", "JPEG", 100, "m1", metadata),
                _make_image("multi", "b.png", "PNG", 200, "m2", metadata),
                _make_image("multi", "c.gif", "GIF", 300, "m3", metadata),
            ]
        )
        paths = download_images(result, tmp_path / "output")

        assert len(paths) == 3
        names = {p.name for p in paths}
        assert names == {"a.jpg", "b.png", "c.gif"}

        meta_path = tmp_path / "output" / "multi" / "metadata.json"
        meta = json.loads(meta_path.read_text())
        assert len(meta["files"]) == 3

    @patch("lomax.util.requests.get")
    def test_partial_download_failure(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() skips failed files, keeps others."""
        good_resp = MagicMock()
        good_resp.raise_for_status = MagicMock()
        good_resp.content = b"good-bytes"

        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = Exception("404")

        mock_get.side_effect = [good_resp, bad_resp]

        metadata = {"identifier": "partial", "title": "Partial"}
        result = _make_result(
            images=[
                _make_image("partial", "good.jpg", metadata=metadata),
                _make_image("partial", "bad.png", "PNG", metadata=metadata),
            ]
        )
        paths = download_images(result, tmp_path / "output")

        assert len(paths) == 1
        assert paths[0].name == "good.jpg"

        meta_path = tmp_path / "output" / "partial" / "metadata.json"
        meta = json.loads(meta_path.read_text())
        assert len(meta["files"]) == 1
        assert meta["files"][0]["name"] == "good.jpg"

    @patch("lomax.util.requests.get")
    def test_all_downloads_fail(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() returns empty list on total failure."""
        mock_get.side_effect = Exception("Network error")

        result = _make_result(images=[_make_image(identifier="all-fail")])
        paths = download_images(result, tmp_path / "output")

        assert paths == []
        # No metadata.json should be written
        meta_path = tmp_path / "output" / "all-fail" / "metadata.json"
        assert not meta_path.exists()

    @patch("lomax.util.requests.get")
    def test_empty_result(
        self,
        mock_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test download_images() with no images returns empty list."""
        result = _make_result(images=[])
        paths = download_images(result, tmp_path / "output")

        assert paths == []
        mock_get.assert_not_called()
