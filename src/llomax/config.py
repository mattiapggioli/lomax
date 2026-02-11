"""Configuration defaults for Llomax."""

from dataclasses import dataclass


@dataclass
class LlomaxConfig:
    """Central configuration with library-level defaults.

    Attributes:
        output_dir: Directory to save downloaded images.
        max_results: Maximum number of search results.
        collections: Restrict searches to these IA collections.
        commercial_use: If True, restrict to commercial-use licenses.
        filters: Arbitrary IA field filters.
    """

    output_dir: str = "llomax_output"
    max_results: int = 10
    collections: list[str] | None = None
    commercial_use: bool = False
    filters: dict[str, str | list[str]] | None = None
