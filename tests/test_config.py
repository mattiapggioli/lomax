"""Tests for LlomaxConfig."""

from llomax.config import LlomaxConfig


class TestLlomaxConfigDefaults:
    """Tests for LlomaxConfig default values."""

    def test_default_output_dir(self) -> None:
        """Test default output_dir is 'llomax_output'."""
        config = LlomaxConfig()
        assert config.output_dir == "llomax_output"

    def test_default_max_results(self) -> None:
        """Test default max_results is 10."""
        config = LlomaxConfig()
        assert config.max_results == 10


class TestLlomaxConfigOverride:
    """Tests for overriding LlomaxConfig values."""

    def test_override_output_dir(self) -> None:
        """Test overriding output_dir."""
        config = LlomaxConfig(output_dir="/tmp/custom")
        assert config.output_dir == "/tmp/custom"

    def test_override_max_results(self) -> None:
        """Test overriding max_results."""
        config = LlomaxConfig(max_results=50)
        assert config.max_results == 50

    def test_override_all(self) -> None:
        """Test overriding all values."""
        config = LlomaxConfig(
            output_dir="~/images",
            max_results=25,
        )
        assert config.output_dir == "~/images"
        assert config.max_results == 25
