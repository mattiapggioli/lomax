"""Lomax - Image retrieval from Internet Archive."""

from lomax.config import LomaxConfig
from lomax.lomax import Lomax
from lomax.result import ImageResult, LomaxResult
from lomax.util import download_images

__version__ = "0.1.0"

__all__ = [
    "ImageResult",
    "Lomax",
    "LomaxConfig",
    "LomaxResult",
    "download_images",
]
