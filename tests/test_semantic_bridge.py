"""Tests for the semantic bridge."""

import pytest

from lomax.semantic_bridge import extract_keywords


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_single_keyword(self) -> None:
        """Test prompt with no commas returns single keyword."""
        assert extract_keywords("jazz") == ["jazz"]

    def test_comma_separated_keywords(self) -> None:
        """Test prompt with commas splits into keywords."""
        result = extract_keywords("jazz, musicians, 1950s")
        assert result == ["jazz", "musicians", "1950s"]

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from each keyword."""
        result = extract_keywords("  jazz ,  musicians  , 1950s  ")
        assert result == ["jazz", "musicians", "1950s"]

    def test_empty_prompt_raises_error(self) -> None:
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            extract_keywords("")

    def test_whitespace_only_prompt_raises_error(self) -> None:
        """Test that whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            extract_keywords("   ")

    def test_filters_empty_segments(self) -> None:
        """Test that empty segments from extra commas are filtered."""
        result = extract_keywords("jazz,,musicians,")
        assert result == ["jazz", "musicians"]
