"""Internet Archive client for image retrieval."""

from dataclasses import dataclass
from enum import StrEnum
from itertools import islice

import internetarchive as ia


class MainCollection(StrEnum):
    """Well-known Internet Archive image collections."""

    NASA = "nasa"
    PRELINGER_ARCHIVES = "prelinger"
    SMITHSONIAN = "smithsonian"
    METROPOLITAN_MUSEUM = "metropolitanmuseumofart-gallery"
    FLICKR_COMMONS = "flickr-commons"
    LIBRARY_OF_CONGRESS = "library_of_congress"


COMMERCIAL_USE_LICENSES = {
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/publicdomain/mark/1.0/",
    "https://creativecommons.org/licenses/by/2.0/",
    "https://creativecommons.org/licenses/by/2.5/",
    "https://creativecommons.org/licenses/by/3.0/",
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by-sa/2.0/",
    "https://creativecommons.org/licenses/by-sa/2.5/",
    "https://creativecommons.org/licenses/by-sa/3.0/",
    "https://creativecommons.org/licenses/by-sa/4.0/",
}


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
        collections: list[MainCollection] | None = None,
        commercial_use: bool = False,
        filters: dict[str, str | list[str]] | None = None,
    ) -> list[SearchResult]:
        """Search the Internet Archive for items matching the keywords.

        Args:
            keywords: List of keywords to search for.
            max_results: Maximum number of results to return.
            operator: Logical operator to join keywords.
                Must be "AND" or "OR". Defaults to "AND".
            collections: Restrict results to these IA collections.
            commercial_use: If True, restrict to commercial-use
                licenses.
            filters: Arbitrary IA field filters. Keys are field
                names, values are strings or lists of strings.
                Shortcut params (collections, commercial_use)
                take precedence over matching keys here.

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

        filter_clauses = self._build_filter_clauses(
            collections, commercial_use, filters
        )
        query = self._build_query(keywords, operator, filter_clauses)
        results = self._execute_search(query, max_results)
        return results

    def _build_filter_clauses(
        self,
        collections: list[MainCollection] | None,
        commercial_use: bool,
        filters: dict[str, str | list[str]] | None,
    ) -> list[str]:
        """Build filter clauses for the IA search query.

        Args:
            collections: Restrict to these IA collections.
            commercial_use: If True, restrict to commercial-use
                licenses.
            filters: Arbitrary IA field filters.

        Returns:
            List of query clause strings.
        """
        clauses: list[str] = []
        handled_keys: set[str] = set()

        if collections:
            handled_keys.add("collection")
            values = " OR ".join(str(c) for c in collections)
            clauses.append(f"collection:({values})")

        if commercial_use:
            handled_keys.add("licenseurl")
            urls = " OR ".join(
                f'"{u}"' for u in sorted(COMMERCIAL_USE_LICENSES)
            )
            clauses.append(f"licenseurl:({urls})")

        if filters:
            for key, value in filters.items():
                if key in handled_keys:
                    continue
                if isinstance(value, list):
                    joined = " OR ".join(value)
                    clauses.append(f"{key}:({joined})")
                else:
                    clauses.append(f"{key}:{value}")

        return clauses

    def _build_query(
        self,
        keywords: list[str],
        operator: str,
        filter_clauses: list[str] | None = None,
    ) -> str:
        """Build an Internet Archive search query from keywords.

        Args:
            keywords: List of keywords to include in the query.
            operator: Logical operator ("AND" or "OR") to join
                keywords.
            filter_clauses: Additional filter clauses to AND-join
                into the query.

        Returns:
            Formatted query string for the IA search API.
        """
        keyword_query = f" {operator} ".join(keywords)
        parts = [
            f"({keyword_query})",
            f"mediatype:{self.mediatype}",
        ]
        if filter_clauses:
            parts.extend(filter_clauses)
        return " AND ".join(parts)

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
        return [
            SearchResult(
                identifier=item.get("identifier", ""),
                title=item.get("title", ""),
                description=item.get("description"),
                mediatype=item.get("mediatype"),
            )
            for item in islice(search, max_results)
        ]
