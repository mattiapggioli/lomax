"""Lomax orchestrator: prompt → keywords → search → structured results."""

import logging

import internetarchive as ia

from lomax.ia_client import IAClient
from lomax.result import ImageResult, LomaxResult
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


class Lomax:
    """Orchestrates prompt → keywords → search → image results."""

    def __init__(self, max_results: int = 10) -> None:
        """Initialize the Lomax orchestrator.

        Args:
            max_results: Maximum number of search results.
        """
        self.max_results = max_results
        self._client = IAClient()

    def search(self, prompt: str) -> LomaxResult:
        """Search the Internet Archive for images matching a prompt.

        Runs the pipeline: prompt → keywords → IA search → image
        filtering. Does not download any files.

        Args:
            prompt: Natural language prompt.

        Returns:
            LomaxResult with all matching image files.

        Raises:
            ValueError: If prompt is empty.
        """
        keywords = extract_keywords(prompt)
        search_results = self._client.search(
            keywords, max_results=self.max_results
        )

        images: list[ImageResult] = []
        for sr in search_results:
            item_images = self._get_item_images(sr.identifier)
            images.extend(item_images)

        return LomaxResult(
            prompt=prompt,
            keywords=keywords,
            images=images,
        )

    def _get_item_images(self, identifier: str) -> list[ImageResult]:
        """Fetch image file info for a single IA item.

        Args:
            identifier: IA item identifier.

        Returns:
            List of ImageResult for image files found, or empty
            list if the item can't be fetched or has no images.
        """
        try:
            item = ia.get_item(identifier)
        except Exception:
            logger.warning("Failed to get item: %s", identifier)
            return []

        metadata = {
            "identifier": item.metadata.get("identifier", ""),
            "title": item.metadata.get("title", ""),
            "description": item.metadata.get("description", ""),
            "creator": item.metadata.get("creator"),
            "date": item.metadata.get("date"),
            "year": item.metadata.get("year"),
            "subject": item.metadata.get("subject"),
            "collection": item.metadata.get("collection"),
            "licenseurl": item.metadata.get("licenseurl"),
            "rights": item.metadata.get("rights"),
            "publisher": item.metadata.get("publisher"),
        }

        results: list[ImageResult] = []
        for f in item.files:
            if f.get("format") not in IMAGE_FORMATS:
                continue
            name = f["name"]
            results.append(
                ImageResult(
                    identifier=identifier,
                    filename=name,
                    download_url=(
                        f"https://archive.org/download/{identifier}/{name}"
                    ),
                    format=f["format"],
                    size=int(f.get("size", 0)),
                    md5=f.get("md5", ""),
                    metadata=metadata,
                )
            )

        return results
