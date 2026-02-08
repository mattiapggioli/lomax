"""Lomax - Image retrieval from Internet Archive."""

from lomax.config import LomaxConfig
from lomax.ia_client import MainCollection
from lomax.lomax import Lomax
from lomax.result import ImageResult, LomaxResult
from lomax.util import download_images

__version__ = "0.1.0"

__all__ = [
    "ImageResult",
    "Lomax",
    "LomaxConfig",
    "LomaxResult",
    "MainCollection",
    "download_images",
]
