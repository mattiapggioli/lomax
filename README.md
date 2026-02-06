# Lomax

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
from lomax import Lomax, download_images

lx = Lomax(max_results=5)

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

## Output structure

```
my_images/
  <identifier>/
    image1.jpg
    image2.png
    metadata.json
```
