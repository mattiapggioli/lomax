"""Semantic bridge: converts natural language prompts into search keywords."""


def extract_keywords(prompt: str) -> list[str]:
    """Extract search keywords from a user prompt.

    Splits the prompt by commas and strips whitespace from each keyword.

    Args:
        prompt: The user's natural language prompt.

    Returns:
        List of keyword strings.

    Raises:
        ValueError: If prompt is empty or whitespace-only.

    NOTE: This is a temporary implementation.
    """
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    keywords = [k.strip() for k in prompt.split(",") if k.strip()]
    return keywords
