"""Configuration defaults for Lomax."""

from dataclasses import dataclass


@dataclass
class LomaxConfig:
    """Central configuration with library-level defaults.

    Attributes:
        output_dir: Directory to save downloaded images.
        max_results: Maximum number of search results.
    """

    output_dir: str = "lomax_output"
    max_results: int = 10
