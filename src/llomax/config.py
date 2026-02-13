"""Configuration defaults for Llomax."""

from dataclasses import dataclass


@dataclass
class LlomaxConfig:
    """Central configuration with library-level defaults.

    Attributes:
        output_dir: Directory to save downloaded images.
        max_results: Maximum number of search results.
        commercial_use: If True, restrict to commercial-use licenses.
    """

    output_dir: str = "llomax_output"
    max_results: int = 10
    commercial_use: bool = False
