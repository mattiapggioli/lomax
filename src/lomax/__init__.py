"""Lomax - Image retrieval from Internet Archive."""

from lomax.lomax import Lomax
from lomax.result import ImageResult, LomaxResult
from lomax.util import download_images

__version__ = "0.1.0"

__all__ = [
    "ImageResult",
    "Lomax",
    "LomaxResult",
    "download_images",
]
