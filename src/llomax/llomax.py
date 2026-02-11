"""Llomax orchestrator: prompt -> keywords -> search -> structured results."""

from concurrent.futures import ThreadPoolExecutor
from itertools import islice

from more_itertools import roundrobin, unique_everseen

from llomax.config import LlomaxConfig
from llomax.ia_client import IAClient, SearchResult
from llomax.result import ImageResult, LlomaxResult
from llomax.semantic_bridge import extract_keywords


class Llomax:
    """Orchestrates prompt -> keywords -> search -> image results."""

    def __init__(self, config: LlomaxConfig | None = None) -> None:
        """Initialize the Llomax orchestrator.

        Args:
            config: Configuration for search parameters. If None,
                library defaults are used.
        """
        if config is None:
            config = LlomaxConfig()
        self.max_results = config.max_results
        self.collections = config.collections
        self.commercial_use = config.commercial_use
        self.filters = config.filters
        self._client = IAClient()

    def search(
        self, prompt: str, max_results: int | None = None
    ) -> LlomaxResult:
        """Search the Internet Archive for images matching a prompt.

        Uses a scatter-gather strategy: searches each keyword
        individually in parallel, then combines results via
        round-robin sampling with deduplication. Item image
        fetches are also parallelized.

        Args:
            prompt: Natural language prompt.
            max_results: Override for the maximum number of results.
                If None, the default from initialization is used.

        Returns:
            LlomaxResult with balanced, de-duplicated image files.

        Raises:
            ValueError: If prompt is empty.
        """
        keywords = extract_keywords(prompt)
        limit = max_results if max_results is not None else self.max_results
        per_keyword_limit = limit * 2

        candidates = self._parallel_search(keywords, per_keyword_limit)

        selected = self._round_robin_sample(candidates, limit=limit)

        images = self._parallel_fetch_images(selected)

        return LlomaxResult(
            prompt=prompt,
            keywords=keywords,
            images=images,
        )

    def _parallel_search(
        self,
        keywords: list[str],
        per_keyword_limit: int,
    ) -> list[list[SearchResult]]:
        """Search IA for each keyword in parallel.

        Args:
            keywords: List of keywords to search.
            per_keyword_limit: Max results per keyword search.

        Returns:
            Per-keyword lists of search results.
        """
        if not keywords:
            return []

        def search_one(kw: str) -> list[SearchResult]:
            return self._client.search(
                [kw],
                max_results=per_keyword_limit,
                collections=self.collections,
                commercial_use=self.commercial_use,
                filters=self.filters,
            )

        workers = min(len(keywords), 8)
        with ThreadPoolExecutor(max_workers=workers) as exe:
            return list(exe.map(search_one, keywords))

    def _parallel_fetch_images(
        self,
        selected: list[SearchResult],
    ) -> list[ImageResult]:
        """Fetch item images in parallel, preserving order.

        Args:
            selected: Search results to fetch images for.

        Returns:
            Flat list of ImageResult across all items.
        """
        if not selected:
            return []

        workers = min(len(selected), 8)
        with ThreadPoolExecutor(max_workers=workers) as exe:
            nested = list(
                exe.map(
                    self._client.get_item_images,
                    [sr.identifier for sr in selected],
                )
            )
        return [img for imgs in nested for img in imgs]

    def _round_robin_sample(
        self,
        candidates: list[list[SearchResult]],
        limit: int,
    ) -> list[SearchResult]:
        """De-duplicating round-robin sample across keyword lists.

        Interleaves candidate lists in round-robin order,
        removes duplicates by identifier, and caps at the
        specified limit.

        Args:
            candidates: Per-keyword lists of search results.
            limit: The maximum number of results to return.

        Returns:
            Balanced, de-duplicated list of SearchResult.
        """
        stream = roundrobin(*candidates)
        unique = unique_everseen(stream, key=lambda sr: sr.identifier)
        return list(islice(unique, limit))
