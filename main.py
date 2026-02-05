"""Run Lomax from the command line."""

import argparse
import sys

from lomax import Lomax


def main() -> None:
    """Parse arguments and run the Lomax pipeline."""
    parser = argparse.ArgumentParser(
        description=("Search and download images from the Internet Archive."),
    )
    parser.add_argument(
        "prompt",
        help="comma-separated keywords to search for",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="lomax_output",
        help="directory to save downloaded images (default: lomax_output)",
    )
    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=10,
        help="maximum number of items to download (default: 10)",
    )
    args = parser.parse_args()

    lx = Lomax(output_dir=args.output_dir, max_results=args.max_results)
    results = lx.run(args.prompt)

    if not results:
        print("No images found.")
        sys.exit(0)

    for r in results:
        print(f"{r.identifier}: {r.files_downloaded} file(s) -> {r.directory}")


if __name__ == "__main__":
    main()
