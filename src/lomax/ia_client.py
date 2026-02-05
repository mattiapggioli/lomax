"""Internet Archive client for image retrieval."""

from dataclasses import dataclass

import internetarchive as ia


@dataclass
class SearchResult:
    """Represents a search result from the Internet Archive."""

    identifier: str
    title: str
    description: str | None = None
    mediatype: str | None = None


class IAClient:
    """Client for searching and retrieving images from the Internet Archive."""

    def __init__(self, mediatype: str = "image") -> None:
        """Initialize the IA client.

        Args:
            mediatype: The type of media to search for. Defaults to "image".
        """
        self.mediatype = mediatype

    def search(
        self,
        keywords: list[str],
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search the Internet Archive for items matching the keywords.

        Args:
            keywords: List of keywords to search for.
            max_results: Maximum number of results to return. Defaults to 10.

        Returns:
            List of SearchResult objects matching the query.

        Raises:
            ValueError: If keywords list is empty.
        """
        if not keywords:
            raise ValueError("Keywords cannot be empty")

        query = self._build_query(keywords)
        results = self._execute_search(query, max_results)
        return results

    def _build_query(self, keywords: list[str]) -> str:
        """Build an Internet Archive search query from keywords.

        Args:
            keywords: List of keywords to include in the query.

        Returns:
            Formatted query string for the IA search API.
        """
        keyword_query = " AND ".join(keywords)
        return f"({keyword_query}) AND mediatype:{self.mediatype}"

    def _execute_search(
        self, query: str, max_results: int
    ) -> list[SearchResult]:
        """Execute the search query against the Internet Archive.

        Args:
            query: The formatted search query.
            max_results: Maximum number of results to return.

        Returns:
            List of SearchResult objects.
        """
        search = ia.search_items(query)
        results: list[SearchResult] = []

        for item in search:
            if len(results) >= max_results:
                break

            result = SearchResult(
                identifier=item.get("identifier", ""),
                title=item.get("title", ""),
                description=item.get("description"),
                mediatype=item.get("mediatype"),
            )
            results.append(result)

        return results
