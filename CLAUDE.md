# Lomax

An image retrieval tool that fetches images from the Internet Archive based on natural language prompts.

## Overview

Lomax takes a user prompt and returns a set of images from the Internet Archive. It works in two stages:

1. **Semantic Bridge (LLM)**: Converts natural language prompts into effective search keywords
2. **Image Retrieval**: Uses the `ia` library to search the Internet Archive and fetch matching images

### Example Flow

```
User prompt: "jazz musicians in the 1950s"
    ↓
LLM Semantic Bridge → keywords: ["jazz", "bebop", "musicians", "1950s"]
    ↓
Internet Archive search via `ia` library
    ↓
Returns images matching the query
```

## Dependencies

- **ia**: Internet Archive Python library for searching and downloading
- **LLM integration**: For prompt-to-keyword semantic translation (TBD)

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: uv
- **Testing**: pytest
- **Linting/Formatting**: Ruff

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Run CLI (once implemented)
uv run lomax
```

## Project Structure

```
lomax/
├── src/lomax/        # Main package source code
│   ├── __init__.py
│   └── cli.py        # CLI entry point
├── tests/            # Test files
├── pyproject.toml    # Project configuration
└── CLAUDE.md
```

## Development Workflow

Follow TDD (Test-Driven Development):
1. **Write tests first** - Define expected behavior in tests before implementation
2. **Write the implementation** - Make the tests pass
3. **Run tests** - Verify with `uv run pytest`
4. **Lint and format** - Run `uv run ruff check . && uv run ruff format .`

## Code Conventions

- Use type hints for function signatures
- Follow PEP 8 style (enforced by Ruff)
- Write docstrings for public functions and classes
- Keep functions focused and small
- Tests go in `tests/` directory, mirroring `src/` structure
