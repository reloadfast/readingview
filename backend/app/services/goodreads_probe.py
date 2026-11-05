"""Read-only Goodreads access/parsing experiment; not wired into the application."""

import argparse
import asyncio
import json
from pathlib import Path

from .goodreads import MAX_BYTES, canonical_url, parse_page, probe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public HTTPS Goodreads book URL")
    parser.add_argument("--html", type=Path, help="Parse a saved HTML file instead of fetching")
    args = parser.parse_args()
    try:
        url = canonical_url(args.url)
        if args.html:
            with args.html.open("rb") as handle:
                content = handle.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                parser.error("Saved HTML exceeds the 5 MiB limit.")
            result = parse_page(content.decode("utf-8", errors="replace"), url)
        else:
            result = asyncio.run(probe(url))
    except (ValueError, OSError, RecursionError) as exc:
        parser.error(
            f"Unable to read input ({type(exc).__name__}). "
            "Use a Goodreads book URL and readable HTML."
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"ok", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
