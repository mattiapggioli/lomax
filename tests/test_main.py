"""Tests for cli_utils.py configuration loading and merging."""

import argparse
from pathlib import Path

from cli_utils import (
    _build_config,
    _load_toml,
)
from llomax.config import LlomaxConfig


def _make_args(**overrides: object) -> argparse.Namespace:
    """Build a Namespace with CLI defaults, applying overrides."""
    defaults = {
        "output_dir": None,
        "max_results": None,
        "commercial_use": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class TestLoadToml:
    """Tests for _load_toml()."""

    def test_returns_empty_dict_when_file_missing(
        self, tmp_path: Path
    ) -> None:
        """Test _load_toml returns {} for a non-existent file."""
        result = _load_toml(tmp_path / "nope.toml")
        assert result == {}

    def test_reads_llomax_section(self, tmp_path: Path) -> None:
        """Test _load_toml reads values from [llomax] section."""
        toml_file = tmp_path / "llomax.toml"
        toml_file.write_text(
            '[llomax]\noutput_dir = "custom"\nmax_results = 5\n'
        )
        result = _load_toml(toml_file)
        assert result == {
            "output_dir": "custom",
            "max_results": 5,
        }

    def test_returns_empty_dict_when_no_llomax_section(
        self, tmp_path: Path
    ) -> None:
        """Test _load_toml returns {} when [llomax] is absent."""
        toml_file = tmp_path / "other.toml"
        toml_file.write_text('[other]\nkey = "value"\n')
        result = _load_toml(toml_file)
        assert result == {}


class TestBuildConfig:
    """Tests for _build_config() layered merging."""

    def test_defaults_only(self) -> None:
        """No TOML, no CLI -> library defaults."""
        config = _build_config({}, _make_args())
        assert config.output_dir == "llomax_output"
        assert config.max_results == 10

    def test_toml_overrides_defaults(self) -> None:
        """TOML values override library defaults."""
        config = _build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            _make_args(),
        )
        assert config.output_dir == "toml_dir"
        assert config.max_results == 20

    def test_cli_overrides_toml(self) -> None:
        """CLI values override TOML values."""
        config = _build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            _make_args(output_dir="cli_dir", max_results=99),
        )
        assert config.output_dir == "cli_dir"
        assert config.max_results == 99

    def test_cli_overrides_defaults(self) -> None:
        """CLI values override library defaults (no TOML)."""
        config = _build_config(
            {},
            _make_args(output_dir="cli_dir", max_results=5),
        )
        assert config.output_dir == "cli_dir"
        assert config.max_results == 5

    def test_partial_toml_override(self) -> None:
        """TOML overrides only the keys it contains."""
        config = _build_config(
            {"max_results": 25},
            _make_args(),
        )
        assert config.output_dir == "llomax_output"
        assert config.max_results == 25

    def test_partial_cli_override(self) -> None:
        """CLI overrides only the arguments provided."""
        config = _build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            _make_args(max_results=3),
        )
        assert config.output_dir == "toml_dir"
        assert config.max_results == 3

    def test_returns_llomax_config(self) -> None:
        """_build_config returns a LlomaxConfig instance."""
        config = _build_config({}, _make_args())
        assert isinstance(config, LlomaxConfig)

    def test_defaults_include_commercial_use(self) -> None:
        """No TOML, no CLI -> commercial_use defaults to False."""
        config = _build_config({}, _make_args())
        assert config.commercial_use is False

    def test_toml_overrides_commercial_use(self) -> None:
        """TOML value overrides commercial_use default."""
        toml = {"commercial_use": True}
        config = _build_config(toml, _make_args())
        assert config.commercial_use is True

    def test_cli_overrides_commercial_use(self) -> None:
        """CLI value overrides TOML commercial_use."""
        toml = {"commercial_use": True}
        config = _build_config(
            toml,
            _make_args(commercial_use=False),
        )
        assert config.commercial_use is False

    def test_partial_cli_preserves_toml_commercial_use(
        self,
    ) -> None:
        """TOML commercial_use preserved without CLI override."""
        toml = {"commercial_use": True}
        config = _build_config(toml, _make_args())
        assert config.commercial_use is True
