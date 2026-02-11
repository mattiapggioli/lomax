"""Run Llomax from the command line."""

import sys

from cli_utils import get_cli_config
from llomax import Llomax, download_images


def main() -> None:
    """Parse arguments and run the Llomax pipeline."""
    prompt, config = get_cli_config()

    lx = Llomax(config)
    result = lx.search(prompt)

    if not result.images:
        print("No images found.")
        sys.exit(0)

    print(
        f"Found {result.total_images} image(s)"
        f" across {result.total_items} item(s)."
    )

    paths = download_images(result, config.output_dir)
    print(f"Downloaded {len(paths)} file(s) to {config.output_dir}/")


if __name__ == "__main__":
    main()
