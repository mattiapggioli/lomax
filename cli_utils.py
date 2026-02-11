"""Command-line interface for Lomax."""

import argparse
import tomllib
from pathlib import Path

from lomax import LomaxConfig

DEFAULT_CONFIG_PATH = Path("lomax.toml")


def _load_toml(path: Path) -> dict:
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


def _parse_filters(
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


def _build_config(
    toml_values: dict,
    cli_args: argparse.Namespace,
) -> LomaxConfig:
    """Build a LomaxConfig with layered overrides.

    Priority: CLI args > TOML values > library defaults.

    Args:
        toml_values: Values loaded from the TOML config file.
        cli_args: Parsed arguments from the command line.

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
    if cli_args.output_dir is not None:
        config.output_dir = cli_args.output_dir
    if cli_args.max_results is not None:
        config.max_results = cli_args.max_results
    if cli_args.collections is not None:
        config.collections = cli_args.collections
    if cli_args.commercial_use is not None:
        config.commercial_use = cli_args.commercial_use

    cli_filters = _parse_filters(cli_args.filters)
    if cli_filters is not None:
        config.filters = cli_filters

    return config


def get_cli_config() -> tuple[str, LomaxConfig]:
    """Parse command-line arguments and build a LomaxConfig."""
    parser = argparse.ArgumentParser(
        description=(
            "Search and download images from the Internet Archive."
        ),
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

    config_path = (
        Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    )
    toml_values = _load_toml(config_path)

    config = _build_config(
        toml_values,
        cli_args=args,
    )

    return args.prompt, config
