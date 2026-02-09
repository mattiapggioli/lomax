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


def parse_filters(
    raw: list[str] | None,
) -> dict[str, str | list[str]] | None:
    """Parse repeatable key=value filter strings into a dict.

    Duplicate keys are merged into a list.

    Args:
        raw: List of "key=value" strings, or None.

    Returns:
        Dict mapping field names to values, or None.
    """
    if not raw:
        return None
    result: dict[str, str | list[str]] = {}
    for item in raw:
        key, _, value = item.partition("=")
        if key in result:
            existing = result[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[key] = [existing, value]
        else:
            result[key] = value
    return result


def build_config(
    toml_values: dict,
    cli_output_dir: str | None,
    cli_max_results: int | None,
    cli_collections: list[str] | None = None,
    cli_commercial_use: bool | None = None,
    cli_filters: dict[str, str | list[str]] | None = None,
) -> LomaxConfig:
    """Build a LomaxConfig with layered overrides.

    Priority: CLI args > TOML values > library defaults.

    Args:
        toml_values: Values loaded from the TOML config file.
        cli_output_dir: Output dir from CLI, or None if not given.
        cli_max_results: Max results from CLI, or None if not given.
        cli_collections: Collections from CLI, or None if not given.
        cli_commercial_use: Commercial use flag from CLI, or None.
        cli_filters: Filters from CLI, or None if not given.

    Returns:
        Fully resolved LomaxConfig.
    """
    config = LomaxConfig()

    # Layer 2: TOML overrides library defaults
    if "output_dir" in toml_values:
        config.output_dir = toml_values["output_dir"]
    if "max_results" in toml_values:
        config.max_results = toml_values["max_results"]
    if "collections" in toml_values:
        config.collections = toml_values["collections"]
    if "commercial_use" in toml_values:
        config.commercial_use = toml_values["commercial_use"]
    if "filters" in toml_values:
        config.filters = toml_values["filters"]

    # Layer 3: CLI overrides TOML
    if cli_output_dir is not None:
        config.output_dir = cli_output_dir
    if cli_max_results is not None:
        config.max_results = cli_max_results
    if cli_collections is not None:
        config.collections = cli_collections
    if cli_commercial_use is not None:
        config.commercial_use = cli_commercial_use
    if cli_filters is not None:
        config.filters = cli_filters

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
    parser.add_argument(
        "--collections",
        nargs="+",
        default=None,
        help="restrict to these IA collections",
    )
    parser.add_argument(
        "--commercial-use",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="restrict to commercial-use licenses",
    )
    parser.add_argument(
        "--filter",
        action="append",
        dest="filters",
        default=None,
        help=(
            "IA field filter as key=value"
            " (repeatable, e.g. --filter year=2020)"
        ),
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    toml_values = load_toml(config_path)

    config = build_config(
        toml_values,
        cli_output_dir=args.output_dir,
        cli_max_results=args.max_results,
        cli_collections=args.collections,
        cli_commercial_use=args.commercial_use,
        cli_filters=parse_filters(args.filters),
    )

    lx = Lomax(config)
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
