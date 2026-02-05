# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Lomax

An image retrieval tool that fetches images from the Internet Archive based on natural language prompts. Two-stage pipeline: (1) LLM semantic bridge converts natural language to search keywords, (2) `IAClient` searches the Internet Archive via the `internetarchive` library.

## Commands

```bash
uv sync                                  # Install dependencies
uv run pytest                            # Run all tests
uv run pytest tests/test_ia_client.py    # Run a single test file
uv run pytest -k "test_name"             # Run a single test by name
uv run ruff check .                      # Lint
uv run ruff format .                     # Format
uv run lomax                             # Run CLI
```

## Architecture

- `src/lomax/cli.py` — CLI entry point (registered as `lomax` console script)
- `src/lomax/ia_client.py` — `IAClient` class wraps `internetarchive.search_items()`, returns `SearchResult` dataclasses. Builds IA queries by AND-joining keywords with a mediatype filter.
- LLM semantic bridge (prompt → keywords) is not yet implemented

## Development Workflow

Follow TDD: write tests first, then implement, then run `uv run pytest`, then `uv run ruff check . && uv run ruff format .`

## Code Conventions

- Type hints on all function signatures
- Docstrings on public functions and classes
- Ruff enforces PEP 8 with 79-char line length (rules: E, F, I, W)
- Tests in `tests/` mirroring `src/` structure
