"""Command-line interface for Llomax."""

import argparse
import tomllib
from pathlib import Path

from llomax import LlomaxConfig

DEFAULT_CONFIG_PATH = Path("llomax.toml")


def _load_toml(path: Path) -> dict:
    """Load config from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        Dict of config values from the [llomax] section,
        or empty dict if file not found.
    """
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data.get("llomax", {})


def _build_config(
    toml_values: dict,
    cli_args: argparse.Namespace,
) -> LlomaxConfig:
    """Build a LlomaxConfig with layered overrides.

    Priority: CLI args > TOML values > library defaults.

    Args:
        toml_values: Values loaded from the TOML config file.
        cli_args: Parsed arguments from the command line.

    Returns:
        Fully resolved LlomaxConfig.
    """
    config = LlomaxConfig()

    # Layer 2: TOML overrides library defaults
    if "output_dir" in toml_values:
        config.output_dir = toml_values["output_dir"]
    if "max_results" in toml_values:
        config.max_results = toml_values["max_results"]
    if "commercial_use" in toml_values:
        config.commercial_use = toml_values["commercial_use"]

    # Layer 3: CLI overrides TOML
    if cli_args.output_dir is not None:
        config.output_dir = cli_args.output_dir
    if cli_args.max_results is not None:
        config.max_results = cli_args.max_results
    if cli_args.commercial_use is not None:
        config.commercial_use = cli_args.commercial_use

    return config


def get_cli_config() -> tuple[str, LlomaxConfig]:
    """Parse command-line arguments and build a LlomaxConfig."""
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
        "--commercial-use",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="restrict to commercial-use licenses",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    toml_values = _load_toml(config_path)

    config = _build_config(
        toml_values,
        cli_args=args,
    )

    return args.prompt, config
