"""Lomax orchestrator: prompt → keywords → search → structured results."""

import logging
from itertools import islice

import internetarchive as ia
from more_itertools import roundrobin, unique_everseen

from lomax.ia_client import IAClient, SearchResult
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

        Uses a scatter-gather strategy: searches each keyword
        individually, then combines results via round-robin
        sampling with deduplication.

        Args:
            prompt: Natural language prompt.

        Returns:
            LomaxResult with balanced, de-duplicated image files.

        Raises:
            ValueError: If prompt is empty.
        """
        keywords = extract_keywords(prompt)
        per_keyword_limit = self.max_results * 2

        candidates: list[list[SearchResult]] = []
        for kw in keywords:
            results = self._client.search([kw], max_results=per_keyword_limit)
            candidates.append(results)

        selected = self._round_robin_sample(candidates)

        images: list[ImageResult] = []
        for sr in selected:
            item_images = self._get_item_images(sr.identifier)
            images.extend(item_images)

        return LomaxResult(
            prompt=prompt,
            keywords=keywords,
            images=images,
        )

    def _round_robin_sample(
        self,
        candidates: list[list[SearchResult]],
    ) -> list[SearchResult]:
        """De-duplicating round-robin sample across keyword lists.

        Interleaves candidate lists in round-robin order,
        removes duplicates by identifier, and caps at
        max_results.

        Args:
            candidates: Per-keyword lists of search results.

        Returns:
            Balanced, de-duplicated list of SearchResult.
        """
        stream = roundrobin(*candidates)
        unique = unique_everseen(stream, key=lambda sr: sr.identifier)
        return list(islice(unique, self.max_results))

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
