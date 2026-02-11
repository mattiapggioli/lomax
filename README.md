# Llomax

A Python library for searching and downloading images from the [Internet Archive](https://archive.org) based on keyword prompts.

## What it does

- Converts a comma-separated prompt into search keywords
- Searches the Internet Archive for matching image items (JPEG, PNG, GIF, TIFF, JPEG 2000, Animated GIF)
- Returns structured results with download URLs, formats, sizes, and item metadata
- Convenience `download_images()` utility to save files and `metadata.json` to disk

## Installation

```bash
uv sync
```

## Usage

### As a script

```bash
uv run python main.py "jazz, musicians, 1950s"
uv run python main.py "vintage maps" -o my_images -n 5
```

### As a library

```python
from llomax import Llomax, LlomaxConfig, download_images

lx = Llomax(LlomaxConfig(max_results=5))

# Search only — no files downloaded
result = lx.search("jazz, musicians, 1950s")
print(result.total_images, "images across", result.total_items, "items")

# Inspect results programmatically
for img in result.images:
    print(img.identifier, img.filename, img.download_url)

# Serialize to JSON-compatible dict
data = result.to_dict()

# Download when ready
paths = download_images(result, "my_images")
```

### CLI options

```bash
uv run python main.py "jazz, musicians" \
  --collections nasa smithsonian \
  --commercial-use \
  --filter year=2020 \
  --filter creator=NASA
```

| Flag | Description |
|---|---|
| `--collections` | Restrict to these IA collections (space-separated) |
| `--commercial-use` / `--no-commercial-use` | Restrict to commercial-use-compatible licenses |
| `--filter key=value` | Arbitrary IA field filter (repeatable) |

### Configuration file

`llomax.toml` supports all search parameters:

```toml
[llomax]
output_dir = "~/data/llomax"
max_results = 10
# collections = ["nasa", "smithsonian"]
# commercial_use = false

# [llomax.filters]
# year = "2020"
# date = "[1950-01-01 TO 1959-12-31]"
```

Priority: CLI args > `llomax.toml` > library defaults.

## Output structure

```
my_images/
  <identifier>/
    image1.jpg
    image2.png
    metadata.json
```
