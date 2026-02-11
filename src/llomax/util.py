"""Download utilities for Llomax search results."""

import json
import logging
from pathlib import Path

import requests

from llomax.result import ImageResult, LlomaxResult

logger = logging.getLogger(__name__)


def download_images(
    result: LlomaxResult, output_dir: str | Path
) -> list[Path]:
    """Download image files from a LlomaxResult to disk.

    Creates directories as ``{output_dir}/{identifier}/`` and writes
    a ``metadata.json`` per item alongside the image files.

    Args:
        result: Search result containing images to download.
        output_dir: Root directory to save files into.

    Returns:
        List of Paths to successfully downloaded files.
    """
    output_dir = Path(output_dir).expanduser()
    downloaded: list[Path] = []

    by_identifier: dict[str, list[ImageResult]] = {}
    for img in result.images:
        by_identifier.setdefault(img.identifier, []).append(img)

    for identifier, images in by_identifier.items():
        item_dir = output_dir / identifier
        item_dir.mkdir(parents=True, exist_ok=True)

        item_downloaded: list[ImageResult] = []
        for img in images:
            try:
                resp = requests.get(img.download_url, timeout=30)
                resp.raise_for_status()
            except Exception:
                logger.warning(
                    "Failed to download %s from %s",
                    img.filename,
                    img.identifier,
                )
                continue

            file_path = item_dir / img.filename
            file_path.write_bytes(resp.content)
            downloaded.append(file_path)
            item_downloaded.append(img)

        if item_downloaded:
            meta = dict(item_downloaded[0].metadata)
            meta["files"] = [
                {
                    "name": img.filename,
                    "url": img.download_url,
                    "format": img.format,
                    "size": img.size,
                    "md5": img.md5,
                }
                for img in item_downloaded
            ]
            metadata_path = item_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )

    return downloaded
