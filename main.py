"""Run Lomax from the command line."""

import argparse
import sys
import tomllib
from pathlib import Path

from lomax import Lomax

DEFAULTS = {
    "output_dir": "lomax_output",
    "max_results": 10,
}

CONFIG_PATH = Path("lomax.toml")


def load_config(path: Path) -> dict:
    """Load config from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        Dict of config values from the [lomax] section,
        or empty dict if file not found.
    """
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data.get("lomax", {})


def main() -> None:
    """Parse arguments and run the Lomax pipeline."""
    parser = argparse.ArgumentParser(
        description=("Search and download images from the Internet Archive."),
    )
    parser.add_argument(
        "prompt",
        help="comma-separated keywords to search for",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="directory to save downloaded images (default: lomax_output)",
    )
    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=None,
        help="maximum number of items to download (default: 10)",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help=f"path to config file (default: {CONFIG_PATH})",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else CONFIG_PATH
    config = load_config(config_path)

    output_dir = (
        args.output_dir or config.get("output_dir") or DEFAULTS["output_dir"]
    )
    max_results = (
        args.max_results
        if args.max_results is not None
        else config.get("max_results", DEFAULTS["max_results"])
    )

    lx = Lomax(output_dir=output_dir, max_results=max_results)
    results = lx.run(args.prompt)

    if not results:
        print("No images found.")
        sys.exit(0)

    for r in results:
        print(f"{r.identifier}: {r.files_downloaded} file(s) -> {r.directory}")


if __name__ == "__main__":
    main()
