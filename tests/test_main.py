"""Tests for main.py configuration loading and merging."""

from pathlib import Path

from lomax.config import LomaxConfig
from main import build_config, load_toml, parse_filters


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

    def test_defaults_include_new_fields(self) -> None:
        """No TOML, no CLI → library defaults for new fields."""
        config = build_config({}, None, None)
        assert config.collections is None
        assert config.commercial_use is False
        assert config.operator == "AND"
        assert config.filters is None

    def test_toml_overrides_new_fields(self) -> None:
        """TOML values override library defaults for new fields."""
        toml = {
            "collections": ["nasa", "smithsonian"],
            "commercial_use": True,
            "operator": "OR",
            "filters": {"year": "2020"},
        }
        config = build_config(toml, None, None)
        assert config.collections == ["nasa", "smithsonian"]
        assert config.commercial_use is True
        assert config.operator == "OR"
        assert config.filters == {"year": "2020"}

    def test_cli_overrides_new_fields(self) -> None:
        """CLI values override TOML for new fields."""
        toml = {
            "collections": ["nasa"],
            "commercial_use": True,
            "operator": "OR",
            "filters": {"year": "2020"},
        }
        config = build_config(
            toml,
            None,
            None,
            cli_collections=["flickr-commons"],
            cli_commercial_use=False,
            cli_operator="AND",
            cli_filters={"creator": "NASA"},
        )
        assert config.collections == ["flickr-commons"]
        assert config.commercial_use is False
        assert config.operator == "AND"
        assert config.filters == {"creator": "NASA"}

    def test_partial_cli_new_fields(self) -> None:
        """CLI overrides only the new fields provided."""
        toml = {
            "collections": ["nasa"],
            "commercial_use": True,
        }
        config = build_config(
            toml,
            None,
            None,
            cli_collections=None,
            cli_commercial_use=None,
            cli_operator="OR",
        )
        assert config.collections == ["nasa"]
        assert config.commercial_use is True
        assert config.operator == "OR"
        assert config.filters is None


class TestParseFilters:
    """Tests for parse_filters() helper."""

    def test_none_input(self) -> None:
        """None input returns None."""
        assert parse_filters(None) is None

    def test_empty_list(self) -> None:
        """Empty list returns None."""
        assert parse_filters([]) is None

    def test_single_values(self) -> None:
        """Single key=value pairs produce string values."""
        result = parse_filters(["year=2020", "creator=NASA"])
        assert result == {"year": "2020", "creator": "NASA"}

    def test_duplicate_keys_merge(self) -> None:
        """Duplicate keys are merged into a list."""
        result = parse_filters(["subject=jazz", "subject=photo", "year=2020"])
        assert result == {
            "subject": ["jazz", "photo"],
            "year": "2020",
        }

    def test_triple_duplicate_keys(self) -> None:
        """Three duplicate keys produce a three-element list."""
        result = parse_filters(["tag=a", "tag=b", "tag=c"])
        assert result == {"tag": ["a", "b", "c"]}
