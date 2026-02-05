# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Lomax

A Python library for searching and downloading images from the Internet Archive based on keyword prompts. Three-stage pipeline: (1) semantic bridge converts prompt to keywords, (2) `IAClient` searches the Internet Archive, (3) `Lomax` orchestrator downloads matching image files with metadata.

## Commands

```bash
uv sync                                  # Install dependencies
uv run pytest                            # Run all tests
uv run pytest tests/test_ia_client.py    # Run a single test file
uv run pytest -k "test_name"             # Run a single test by name
uv run ruff check .                      # Lint
uv run ruff format .                     # Format
uv run python main.py "keywords"         # Run via main.py
```

## Architecture

- `main.py` — Entry point. Parses CLI arguments (`prompt`, `--output-dir`, `--max-results`) and runs the `Lomax` pipeline.
- `src/lomax/lomax.py` — `Lomax` orchestrator: wires the full pipeline (prompt → keywords → search → download). Downloads image files via `requests`, writes `metadata.json` per item. Uses `IMAGE_FORMATS` set to filter IA files. Key dataclasses: `DownloadResult`, `DownloadedFile`.
- `src/lomax/ia_client.py` — `IAClient` wraps `internetarchive.search_items()`, returns `SearchResult` dataclasses. Builds IA queries by AND-joining keywords with a `mediatype` filter.
- `src/lomax/semantic_bridge.py` — `extract_keywords()` converts prompts to keyword lists. Currently a simple comma-split placeholder; intended to be replaced with LLM-based extraction.
- `src/lomax/__init__.py` — Public API exports `Lomax` and `DownloadResult`.

## Development Workflow

Follow TDD: write tests first, then implement, then run `uv run pytest`, then `uv run ruff check . && uv run ruff format .`

## Code Conventions

- Type hints on all function signatures
- Docstrings on public functions and classes
- Ruff enforces PEP 8 with 79-char line length (rules: E, F, I, W)
- Tests in `tests/` mirroring `src/` structure
- Tests mock external dependencies (`internetarchive`, `requests`) via `unittest.mock.patch`
