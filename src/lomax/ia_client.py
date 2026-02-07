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

    VALID_OPERATORS = {"AND", "OR"}

    def search(
        self,
        keywords: list[str],
        max_results: int = 10,
        operator: str = "AND",
    ) -> list[SearchResult]:
        """Search the Internet Archive for items matching the keywords.

        Args:
            keywords: List of keywords to search for.
            max_results: Maximum number of results to return.
            operator: Logical operator to join keywords.
                Must be "AND" or "OR". Defaults to "AND".

        Returns:
            List of SearchResult objects matching the query.

        Raises:
            ValueError: If keywords list is empty or operator
                is unsupported.
        """
        if not keywords:
            raise ValueError("Keywords cannot be empty")
        if operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Unsupported operator: {operator!r}."
                f" Must be one of {self.VALID_OPERATORS}"
            )

        query = self._build_query(keywords, operator)
        results = self._execute_search(query, max_results)
        return results

    def _build_query(self, keywords: list[str], operator: str) -> str:
        """Build an Internet Archive search query from keywords.

        Args:
            keywords: List of keywords to include in the query.
            operator: Logical operator ("AND" or "OR") to join
                keywords.

        Returns:
            Formatted query string for the IA search API.
        """
        keyword_query = f" {operator} ".join(keywords)
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
