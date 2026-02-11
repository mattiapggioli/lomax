"""Llomax - Image retrieval from Internet Archive."""

from llomax.config import LlomaxConfig
from llomax.ia_client import MainCollection
from llomax.llomax import Llomax
from llomax.result import ImageResult, LlomaxResult
from llomax.util import download_images

__version__ = "0.1.0"

__all__ = [
    "ImageResult",
    "Llomax",
    "LlomaxConfig",
    "LlomaxResult",
    "MainCollection",
    "download_images",
]
