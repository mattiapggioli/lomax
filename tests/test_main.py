"""Tests for cli_utils.py configuration loading and merging."""

import argparse
from pathlib import Path

from cli_utils import (
    _build_config,
    _load_toml,
    _parse_filters,
)
from llomax.config import LlomaxConfig


def _make_args(**overrides: object) -> argparse.Namespace:
    """Build a Namespace with CLI defaults, applying overrides."""
    defaults = {
        "output_dir": None,
        "max_results": None,
        "collections": None,
        "commercial_use": None,
        "filters": None,
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

    def test_defaults_include_new_fields(self) -> None:
        """No TOML, no CLI -> library defaults for new fields."""
        config = _build_config({}, _make_args())
        assert config.collections is None
        assert config.commercial_use is False
        assert config.filters is None

    def test_toml_overrides_new_fields(self) -> None:
        """TOML values override library defaults for new fields."""
        toml = {
            "collections": ["nasa", "smithsonian"],
            "commercial_use": True,
            "filters": {"year": "2020"},
        }
        config = _build_config(toml, _make_args())
        assert config.collections == [
            "nasa",
            "smithsonian",
        ]
        assert config.commercial_use is True
        assert config.filters == {"year": "2020"}

    def test_cli_overrides_new_fields(self) -> None:
        """CLI values override TOML for new fields."""
        toml = {
            "collections": ["nasa"],
            "commercial_use": True,
            "filters": {"year": "2020"},
        }
        config = _build_config(
            toml,
            _make_args(
                collections=["flickr-commons"],
                commercial_use=False,
                filters=["creator=NASA"],
            ),
        )
        assert config.collections == ["flickr-commons"]
        assert config.commercial_use is False
        assert config.filters == {"creator": "NASA"}

    def test_partial_cli_new_fields(self) -> None:
        """CLI overrides only the new fields provided."""
        toml = {
            "collections": ["nasa"],
            "commercial_use": True,
        }
        config = _build_config(toml, _make_args())
        assert config.collections == ["nasa"]
        assert config.commercial_use is True
        assert config.filters is None


class TestParseFilters:
    """Tests for _parse_filters() helper."""

    def test_none_input(self) -> None:
        """None input returns None."""
        assert _parse_filters(None) is None

    def test_empty_list(self) -> None:
        """Empty list returns None."""
        assert _parse_filters([]) is None

    def test_single_values(self) -> None:
        """Single key=value pairs produce string values."""
        result = _parse_filters(["year=2020", "creator=NASA"])
        assert result == {
            "year": "2020",
            "creator": "NASA",
        }

    def test_duplicate_keys_merge(self) -> None:
        """Duplicate keys are merged into a list."""
        result = _parse_filters(["subject=jazz", "subject=photo", "year=2020"])
        assert result == {
            "subject": ["jazz", "photo"],
            "year": "2020",
        }

    def test_triple_duplicate_keys(self) -> None:
        """Three duplicate keys produce a three-element list."""
        result = _parse_filters(["tag=a", "tag=b", "tag=c"])
        assert result == {"tag": ["a", "b", "c"]}
