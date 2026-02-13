# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Llomax

A Python library for searching and downloading images from the Internet Archive based on keyword prompts. `Llomax.search()` returns structured results (`LlomaxResult` / `ImageResult`). `download_images()` is a convenience utility to save files to disk.

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

Source lives in `src/llomax/` (hatchling `src` layout, Python >=3.11). Public API: `from llomax import Llomax, LlomaxConfig, LlomaxResult, ImageResult, MainCollection, download_images`.

### Top-level files

- `main.py` — CLI entry point. Calls `Llomax.search()` then `download_images()`.
- `cli_utils.py` — CLI argument parsing and layered config resolution. `get_cli_config()` returns `(prompt, LlomaxConfig)`. Priority: CLI args > `llomax.toml` > library defaults. `_load_toml()` reads the `[llomax]` section from TOML.
- `llomax.toml` — TOML config file with a `[llomax]` section (`output_dir`, `max_results`, `commercial_use`). Loaded via stdlib `tomllib`.

### Library (`src/llomax/`)

- `llomax.py` — `Llomax` orchestrator: scatter-gather search (prompt → keywords → per-keyword IA search → round-robin sampling with dedup → image results → `LlomaxResult`). `__init__()` accepts an optional `LlomaxConfig` (defaults used when None). `search()` accepts an optional `max_results` override. Uses `more_itertools.roundrobin` and `unique_everseen` for balanced results across keywords. No filesystem side effects.
- `ia_client.py` — `IAClient` wraps `internetarchive.search_items()` and `ia.get_item()`. Returns `SearchResult` dataclasses from search and `ImageResult` lists from `get_item_images()`. `MainCollection` StrEnum provides well-known IA image collections (NASA, Smithsonian, Flickr Commons, etc.). `IAClient.search()` supports hybrid filtering: `collections` (any IA collection string), `commercial_use` (restrict to CC-compatible licenses via `COMMERCIAL_USE_LICENSES` set), `filters` (arbitrary IA field filters), and `operator` ("AND"/"OR" keyword joining). `IMAGE_FORMATS` set defines accepted image file types.
- `config.py` — `LlomaxConfig` dataclass with library-level defaults (`output_dir`, `max_results`, `commercial_use`).
- `result.py` — `ImageResult` (single image file with download URL, format, size, md5, item metadata dict) and `LlomaxResult` (prompt, keywords, list of `ImageResult`, `to_dict()` for JSON serialization).
- `util.py` — `download_images(result, output_dir)`: downloads files via `requests.get`, saves to `{output_dir}/{identifier}/{filename}`, writes `metadata.json` per item.
- `semantic_bridge.py` — `extract_keywords()` converts prompts to keyword lists. Currently a simple comma-split placeholder; intended to be replaced with LLM-based extraction.

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

## Test Conventions

- `test_llomax.py` — mocks `_client` (IAClient) only; search has no network/filesystem side effects
- `test_ia_client.py` — **hits the real Internet Archive API** (no mocks); requires network access and may be slow
- `test_util.py` — mocks `requests.get` via `@patch("llomax.util.requests.get")` and uses `tmp_path` for filesystem assertions
- `test_main.py` — tests `cli_utils.py` functions (`_build_config`, `_load_toml`); uses `tmp_path` for TOML file tests
- `test_config.py` — tests `LlomaxConfig` defaults and field overrides
- `test_semantic_bridge.py` — tests `extract_keywords()` comma splitting and `ValueError` on empty input
