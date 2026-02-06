# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Lomax

A Python library for searching and downloading images from the Internet Archive based on keyword prompts. Search and download are decoupled: `Lomax.search()` returns structured data (`LomaxResult` with `ImageResult` objects), and `download_images()` is a separate utility for writing files to disk.

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

Source lives in `src/lomax/` (hatchling `src` layout). Public API: `from lomax import Lomax, LomaxResult, ImageResult, download_images`.

- `main.py` — CLI entry point. Calls `Lomax.search()` then `download_images()`. Parameter priority: CLI args > `lomax.toml` config > hardcoded defaults.
- `lomax.toml` — TOML config file with a `[lomax]` section (`output_dir`, `max_results`). Loaded via stdlib `tomllib`.
- `src/lomax/result.py` — Data structures: `ImageResult` (single image file with download URL, format, size, md5, item metadata dict) and `LomaxResult` (prompt, keywords, list of `ImageResult`, `to_dict()` for JSON serialization).
- `src/lomax/lomax.py` — `Lomax` orchestrator: search-only pipeline (prompt → keywords → IA search → image filtering → `LomaxResult`). No filesystem side effects. Uses `IMAGE_FORMATS` set to filter IA files.
- `src/lomax/util.py` — `download_images(result, output_dir)`: downloads files from `ImageResult.download_url`, saves to `{output_dir}/{identifier}/{filename}`, writes `metadata.json` per item.
- `src/lomax/ia_client.py` — `IAClient` wraps `internetarchive.search_items()`, returns `SearchResult` dataclasses. Builds IA queries by AND-joining keywords with a `mediatype` filter.
- `src/lomax/semantic_bridge.py` — `extract_keywords()` converts prompts to keyword lists. Currently a simple comma-split placeholder; intended to be replaced with LLM-based extraction.

## Development Workflow

Follow TDD: write tests first, then implement, then run `uv run pytest`, then `uv run ruff check . && uv run ruff format .`

## Code Conventions

- Type hints on all function signatures
- Docstrings on public functions and classes
- Ruff enforces PEP 8 with 79-char line length (rules: E, F, I, W)
- Tests in `tests/` mirroring `src/` structure
- Tests mock external dependencies (`internetarchive`, `requests`) via `unittest.mock.patch`
- **Exception:** `tests/test_ia_client.py` hits the real Internet Archive API (no mocks) — these tests require network access and may be slow
