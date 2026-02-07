"""Tests for LomaxConfig."""

from lomax.config import LomaxConfig


class TestLomaxConfigDefaults:
    """Tests for LomaxConfig default values."""

    def test_default_output_dir(self) -> None:
        """Test default output_dir is 'lomax_output'."""
        config = LomaxConfig()
        assert config.output_dir == "lomax_output"

    def test_default_max_results(self) -> None:
        """Test default max_results is 10."""
        config = LomaxConfig()
        assert config.max_results == 10


class TestLomaxConfigOverride:
    """Tests for overriding LomaxConfig values."""

    def test_override_output_dir(self) -> None:
        """Test overriding output_dir."""
        config = LomaxConfig(output_dir="/tmp/custom")
        assert config.output_dir == "/tmp/custom"

    def test_override_max_results(self) -> None:
        """Test overriding max_results."""
        config = LomaxConfig(max_results=50)
        assert config.max_results == 50

    def test_override_all(self) -> None:
        """Test overriding all values."""
        config = LomaxConfig(
            output_dir="~/images",
            max_results=25,
        )
        assert config.output_dir == "~/images"
        assert config.max_results == 25
