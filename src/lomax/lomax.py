"""Lomax orchestrator: prompt → keywords → search → download."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import internetarchive as ia
import requests

from lomax.ia_client import IAClient, SearchResult
from lomax.semantic_bridge import extract_keywords

logger = logging.getLogger(__name__)

IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "GIF",
    "TIFF",
    "JPEG 2000",
    "Animated GIF",
}


@dataclass
class DownloadedFile:
    """Metadata for a single downloaded file."""

    name: str
    url: str
    format: str
    size: int
    md5: str


@dataclass
class DownloadResult:
    """Result of downloading an IA item."""

    identifier: str
    directory: Path
    files_downloaded: int
    metadata_path: Path


class Lomax:
    """Orchestrates prompt → keywords → search → download."""

    def __init__(
        self,
        output_dir: str | Path = "lomax_output",
        max_results: int = 10,
    ) -> None:
        """Initialize the Lomax orchestrator.

        Args:
            output_dir: Directory to save downloaded images.
            max_results: Maximum number of search results.
        """
        self.output_dir = Path(output_dir)
        self.max_results = max_results
        self._client = IAClient()

    def run(self, prompt: str) -> list[DownloadResult]:
        """Run the full pipeline: prompt → keywords → search → download.

        Args:
            prompt: Natural language prompt.

        Returns:
            List of DownloadResult for each successfully downloaded item.

        Raises:
            ValueError: If prompt is empty.
        """
        keywords = extract_keywords(prompt)
        search_results = self._client.search(
            keywords, max_results=self.max_results
        )

        results: list[DownloadResult] = []
        for sr in search_results:
            result = self.download_item(sr)
            if result is not None:
                results.append(result)

        return results

    def download_item(
        self, search_result: SearchResult
    ) -> DownloadResult | None:
        """Download all image files for a single IA item.

        Args:
            search_result: The search result to download.

        Returns:
            DownloadResult if any files were downloaded, None otherwise.
        """
        try:
            item = ia.get_item(search_result.identifier)
        except Exception:
            logger.warning(
                "Failed to get item: %s",
                search_result.identifier,
            )
            return None

        image_files = [
            f for f in item.files if f.get("format") in IMAGE_FORMATS
        ]

        if not image_files:
            return None

        item_dir = self.output_dir / search_result.identifier
        item_dir.mkdir(parents=True, exist_ok=True)

        downloaded: list[DownloadedFile] = []
        for file_meta in image_files:
            name = file_meta["name"]
            url = (
                f"https://archive.org/download/"
                f"{search_result.identifier}/{name}"
            )
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
            except Exception:
                logger.warning(
                    "Failed to download %s from %s",
                    name,
                    search_result.identifier,
                )
                continue

            file_path = item_dir / name
            file_path.write_bytes(resp.content)

            downloaded.append(
                DownloadedFile(
                    name=name,
                    url=url,
                    format=file_meta["format"],
                    size=int(file_meta.get("size", 0)),
                    md5=file_meta.get("md5", ""),
                )
            )

        if not downloaded:
            return None

        metadata = {
            "identifier": item.metadata.get("identifier", ""),
            "title": item.metadata.get("title", ""),
            "description": item.metadata.get("description", ""),
            "files": [
                {
                    "name": df.name,
                    "url": df.url,
                    "format": df.format,
                    "size": df.size,
                    "md5": df.md5,
                }
                for df in downloaded
            ],
        }

        metadata_path = item_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        return DownloadResult(
            identifier=search_result.identifier,
            directory=item_dir,
            files_downloaded=len(downloaded),
            metadata_path=metadata_path,
        )
