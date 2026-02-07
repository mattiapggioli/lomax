"""Run Lomax from the command line."""

import argparse
import sys
import tomllib
from pathlib import Path

from lomax import Lomax, LomaxConfig, download_images

DEFAULT_CONFIG_PATH = Path("lomax.toml")


def load_toml(path: Path) -> dict:
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


def build_config(
    toml_values: dict,
    cli_output_dir: str | None,
    cli_max_results: int | None,
) -> LomaxConfig:
    """Build a LomaxConfig with layered overrides.

    Priority: CLI args > TOML values > library defaults.

    Args:
        toml_values: Values loaded from the TOML config file.
        cli_output_dir: Output dir from CLI, or None if not given.
        cli_max_results: Max results from CLI, or None if not given.

    Returns:
        Fully resolved LomaxConfig.
    """
    config = LomaxConfig()

    # Layer 2: TOML overrides library defaults
    if "output_dir" in toml_values:
        config.output_dir = toml_values["output_dir"]
    if "max_results" in toml_values:
        config.max_results = toml_values["max_results"]

    # Layer 3: CLI overrides TOML
    if cli_output_dir is not None:
        config.output_dir = cli_output_dir
    if cli_max_results is not None:
        config.max_results = cli_max_results

    return config


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
        help="directory to save downloaded images",
    )
    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=None,
        help="maximum number of items to download",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help=(f"path to config file (default: {DEFAULT_CONFIG_PATH})"),
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    toml_values = load_toml(config_path)

    config = build_config(
        toml_values,
        cli_output_dir=args.output_dir,
        cli_max_results=args.max_results,
    )

    lx = Lomax(max_results=config.max_results)
    result = lx.search(args.prompt)

    if not result.images:
        print("No images found.")
        sys.exit(0)

    print(
        f"Found {result.total_images} image(s)"
        f" across {result.total_items} item(s)."
    )

    paths = download_images(result, config.output_dir)
    print(f"Downloaded {len(paths)} file(s) to {config.output_dir}/")


if __name__ == "__main__":
    main()
