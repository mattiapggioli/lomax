# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Lomax

A Python library for searching and downloading images from the Internet Archive based on keyword prompts. `Lomax.search()` returns structured results (`LomaxResult` / `ImageResult`). `download_images()` is a convenience utility to save files to disk.

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

Source lives in `src/lomax/` (hatchling `src` layout). Public API: `from lomax import Lomax, LomaxConfig, LomaxResult, ImageResult, MainCollection, download_images`.

- `main.py` — CLI entry point. Calls `Lomax.search()` then `download_images()`. Parameter priority: CLI args > `lomax.toml` config > hardcoded defaults. CLI supports `--collections`, `--commercial-use`/`--no-commercial-use`, and `--filter` flags. `parse_filters()` converts repeatable `key=value` strings into a dict.
- `lomax.toml` — TOML config file with a `[lomax]` section (`output_dir`, `max_results`, `collections`, `commercial_use`, `filters`). Loaded via stdlib `tomllib`.
- `src/lomax/result.py` — Data structures: `ImageResult` (single image file with download URL, format, size, md5, item metadata dict) and `LomaxResult` (prompt, keywords, list of `ImageResult`, `to_dict()` for JSON serialization).
- `src/lomax/config.py` — `LomaxConfig` dataclass with library-level defaults (`output_dir`, `max_results`, `collections`, `commercial_use`, `filters`). Used by `main.py` for layered config resolution.
- `src/lomax/lomax.py` — `Lomax` orchestrator: scatter-gather search (prompt → keywords → per-keyword IA search → round-robin sampling with dedup → image results → `LomaxResult`). `__init__()` accepts an optional `LomaxConfig` (defaults used when None). `search()` accepts an optional `max_results` override. Uses `more_itertools.roundrobin` and `unique_everseen` for balanced results across keywords. No filesystem side effects.
- `src/lomax/util.py` — `download_images(result, output_dir)`: downloads files from `ImageResult.download_url`, saves to `{output_dir}/{identifier}/{filename}`, writes `metadata.json` per item.
- `src/lomax/ia_client.py` — `IAClient` wraps `internetarchive.search_items()` and `ia.get_item()`. Returns `SearchResult` dataclasses from search and `ImageResult` lists from `get_item_images()`. `MainCollection` StrEnum provides well-known IA image collections (NASA, Smithsonian, Flickr Commons, etc.). `IAClient.search()` supports hybrid filtering: `collections` (any IA collection string), `commercial_use` (restrict to CC-compatible licenses via `COMMERCIAL_USE_LICENSES` set), `filters` (arbitrary IA field filters), and `operator` ("AND"/"OR" keyword joining). `IMAGE_FORMATS` set defines accepted image file types.
- `src/lomax/semantic_bridge.py` — `extract_keywords()` converts prompts to keyword lists. Currently a simple comma-split placeholder; intended to be replaced with LLM-based extraction.

## Development Workflow

Follow TDD: write tests first, then implement, then run `uv run pytest`, then `uv run ruff check . && uv run ruff format .`

## Writing Style

- README and user-facing docs should be practical, not didactic. Describe what things do, don't explain design rationale or architectural justifications.
- Avoid "code lecture" tone (e.g. don't write "X and Y are decoupled for flexibility"). Just state what the API offers.

## Code Conventions

- Type hints on all function signatures
- Docstrings on public functions and classes
- Prefer list comprehensions over for-loop-append patterns when the result is clean and readable
- Ruff enforces PEP 8 with 79-char line length (rules: E, F, I, W)
- Tests in `tests/` mirroring `src/` structure
- `test_lomax.py` mocks `_client` (IAClient) only — search has no network/filesystem side effects
- `test_util.py` mocks `requests.get` and uses `tmp_path` for filesystem assertions
- **Exception:** `test_ia_client.py` hits the real Internet Archive API (no mocks) — requires network access and may be slow
