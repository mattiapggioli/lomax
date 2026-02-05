# Lomax

A Python library for searching and downloading images from the [Internet Archive](https://archive.org) based on keyword prompts.

## What it does

- Converts a comma-separated prompt into search keywords
- Searches the Internet Archive for matching image items
- Downloads image files (JPEG, PNG, GIF, TIFF, JPEG 2000, Animated GIF) from each result
- Saves a `metadata.json` alongside downloaded files with identifiers, titles, descriptions, URLs, sizes, and checksums

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
from lomax import Lomax

lx = Lomax(output_dir="my_images", max_results=5)
results = lx.run("jazz, musicians, 1950s")

for r in results:
    print(r.identifier, r.files_downloaded, r.directory)
```

## Output structure

```
lomax_output/
  <identifier>/
    image1.jpg
    image2.png
    metadata.json
```
