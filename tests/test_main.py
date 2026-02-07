"""Tests for main.py configuration loading and merging."""

from pathlib import Path

from lomax.config import LomaxConfig
from main import build_config, load_toml


class TestLoadToml:
    """Tests for load_toml()."""

    def test_returns_empty_dict_when_file_missing(
        self, tmp_path: Path
    ) -> None:
        """Test load_toml returns {} for a non-existent file."""
        result = load_toml(tmp_path / "nope.toml")
        assert result == {}

    def test_reads_lomax_section(self, tmp_path: Path) -> None:
        """Test load_toml reads values from the [lomax] section."""
        toml_file = tmp_path / "lomax.toml"
        toml_file.write_text(
            '[lomax]\noutput_dir = "custom"\nmax_results = 5\n'
        )
        result = load_toml(toml_file)
        assert result == {"output_dir": "custom", "max_results": 5}

    def test_returns_empty_dict_when_no_lomax_section(
        self, tmp_path: Path
    ) -> None:
        """Test load_toml returns {} when [lomax] is absent."""
        toml_file = tmp_path / "other.toml"
        toml_file.write_text('[other]\nkey = "value"\n')
        result = load_toml(toml_file)
        assert result == {}


class TestBuildConfig:
    """Tests for build_config() layered merging."""

    def test_defaults_only(self) -> None:
        """No TOML, no CLI → library defaults."""
        config = build_config({}, None, None)
        assert config.output_dir == "lomax_output"
        assert config.max_results == 10

    def test_toml_overrides_defaults(self) -> None:
        """TOML values override library defaults."""
        config = build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            None,
            None,
        )
        assert config.output_dir == "toml_dir"
        assert config.max_results == 20

    def test_cli_overrides_toml(self) -> None:
        """CLI values override TOML values."""
        config = build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            cli_output_dir="cli_dir",
            cli_max_results=99,
        )
        assert config.output_dir == "cli_dir"
        assert config.max_results == 99

    def test_cli_overrides_defaults(self) -> None:
        """CLI values override library defaults (no TOML)."""
        config = build_config(
            {},
            cli_output_dir="cli_dir",
            cli_max_results=5,
        )
        assert config.output_dir == "cli_dir"
        assert config.max_results == 5

    def test_partial_toml_override(self) -> None:
        """TOML overrides only the keys it contains."""
        config = build_config(
            {"max_results": 25},
            None,
            None,
        )
        assert config.output_dir == "lomax_output"
        assert config.max_results == 25

    def test_partial_cli_override(self) -> None:
        """CLI overrides only the arguments provided."""
        config = build_config(
            {"output_dir": "toml_dir", "max_results": 20},
            cli_output_dir=None,
            cli_max_results=3,
        )
        assert config.output_dir == "toml_dir"
        assert config.max_results == 3

    def test_returns_lomax_config(self) -> None:
        """build_config returns a LomaxConfig instance."""
        config = build_config({}, None, None)
        assert isinstance(config, LomaxConfig)
