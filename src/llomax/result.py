"""Data structures for Llomax search results."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImageResult:
    """A single image file found on the Internet Archive.

    Args:
        identifier: IA item identifier.
        filename: Name of the image file.
        download_url: Full URL to download the file.
        format: IA format string (e.g. "JPEG", "PNG").
        size: File size in bytes.
        md5: MD5 checksum of the file.
        metadata: Item-level metadata (title, description, etc.).
    """

    identifier: str
    filename: str
    download_url: str
    format: str
    size: int
    md5: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LlomaxResult:
    """Complete search result from the Llomax pipeline.

    Args:
        prompt: The original user prompt.
        keywords: Keywords extracted from the prompt.
        images: List of image files found.
    """

    prompt: str
    keywords: list[str]
    images: list[ImageResult] = field(default_factory=list)

    @property
    def total_images(self) -> int:
        """Total number of image files found."""
        return len(self.images)

    @property
    def total_items(self) -> int:
        """Number of distinct IA items with images."""
        return len({img.identifier for img in self.images})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result to a JSON-compatible dict."""
        return {
            "prompt": self.prompt,
            "keywords": self.keywords,
            "total_items": self.total_items,
            "total_images": self.total_images,
            "images": [
                {
                    "identifier": img.identifier,
                    "filename": img.filename,
                    "download_url": img.download_url,
                    "format": img.format,
                    "size": img.size,
                    "md5": img.md5,
                    "metadata": img.metadata,
                }
                for img in self.images
            ],
        }
