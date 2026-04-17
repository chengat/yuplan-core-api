#!/usr/bin/env python3
"""
Download York SIS timetable HTML into scraping/page_source/<term>/ using
scraping/page_source/catalog_resource_map.json.

Usage:
  python scripts/fetch_page_sources.py --term fall-winter-2026-2027
  python scripts/fetch_page_sources.py --term summer-2026
  python scraping/scrapers/scrape.py --fall-winter-term fall-winter-2026-2027
  python scripts/run_seed_pipeline.py
  python scripts/fetch_page_sources.py --term fall-winter-2025-2026 --only schulich,science
  python scripts/fetch_page_sources.py --term fall-winter-2026-2027 --dry-run
  python scripts/fetch_page_sources.py --term fall-winter-2026-2027 --delay 0
  # If you get Passport York HTML instead of timetables, pass session cookies from a logged-in browser:
  python scripts/fetch_page_sources.py --term fall-winter-2026-2027 --cookie 'name=value; other=...'

Requires network access to apps1.sis.yorku.ca (no extra pip packages).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_map(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def looks_like_passport_block(body: bytes) -> bool:
    """True if response is Passport York / SSO error instead of timetable HTML."""
    if b"Passport York Login" in body or b"Passport York was unable" in body:
        return True
    if b"ppylogin" in body and b"alert-danger" in body:
        return True
    return False


def html_bytes_for_disk(body: bytes) -> bytes:
    """If the response is UTF-16 (some clients), normalize to UTF-8 for scrapers."""
    if body.startswith((b"\xff\xfe", b"\xfe\xff")):
        return body.decode("utf-16").encode("utf-8")
    return body


def fetch_url(
    url: str,
    *,
    timeout: int = 60,
    referer: str = "",
    cookie: str = "",
) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def main() -> int:
    root = repo_root()
    default_map = root / "scraping" / "page_source" / "catalog_resource_map.json"
    default_out = root / "scraping" / "page_source"

    p = argparse.ArgumentParser(description="Fetch SIS timetable HTML into page_source/")
    p.add_argument(
        "--term",
        required=True,
        help="Term folder key, e.g. fall-winter-2026-2027",
    )
    p.add_argument("--map", type=Path, default=default_map, help="Path to catalog_resource_map.json")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=default_out,
        help="page_source root (default: scraping/page_source)",
    )
    p.add_argument(
        "--only",
        default="",
        help="Comma-separated stems to fetch only (e.g. schulich,science)",
    )
    p.add_argument("--dry-run", action="store_true", help="Print URLs only; do not write files")
    p.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds")
    p.add_argument(
        "--delay",
        type=float,
        default=10.0,
        metavar="SEC",
        help="Seconds to wait between HTTP requests (default: 10). Use 0 to disable.",
    )
    p.add_argument(
        "--referer",
        default="https://apps1.sis.yorku.ca/",
        help="Referer header (default: apps1 SIS origin). Empty string disables.",
    )
    p.add_argument(
        "--cookie",
        default="",
        metavar="STRING",
        help="Raw Cookie header value from a logged-in browser session (DevTools → Network → request headers).",
    )
    args = p.parse_args()

    if not args.map.is_file():
        print(f"Map file not found: {args.map}", file=sys.stderr)
        return 1

    data = load_map(args.map)
    base_url = data.get("base_url", "").rstrip("/") + "/"
    terms = data.get("terms") or {}
    if args.term not in terms:
        print(f"Unknown term {args.term!r}. Known: {', '.join(sorted(terms))}", file=sys.stderr)
        return 1

    term_cfg = terms[args.term]
    year_prefix = term_cfg.get("year_prefix")
    stems = term_cfg.get("stem_to_faculty_code") or {}
    if not year_prefix or not stems:
        print(f"Term {args.term!r} missing year_prefix or stem_to_faculty_code", file=sys.stderr)
        return 1

    only = {s.strip() for s in args.only.split(",") if s.strip()}

    dest_dir = args.out_dir / args.term
    if not args.dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    fetch_index = 0
    for stem, code in sorted(stems.items(), key=lambda x: x[0]):
        if only and stem not in only:
            continue
        filename = f"{year_prefix}{code}.html"
        url = base_url + filename
        out_path = dest_dir / f"{stem}.html"

        if args.dry_run:
            print(f"{stem}: {url} -> {out_path.relative_to(root)}")
            continue

        if fetch_index > 0 and args.delay > 0:
            time.sleep(args.delay)
        fetch_index += 1

        try:
            body = fetch_url(
                url,
                timeout=args.timeout,
                referer=(args.referer or ""),
                cookie=(args.cookie or ""),
            )
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} {stem}: {url}", file=sys.stderr)
            errors += 1
            continue
        except urllib.error.URLError as e:
            print(f"URL error {stem}: {e.reason!r} ({url})", file=sys.stderr)
            errors += 1
            continue
        except Exception as e:
            print(f"Error {stem}: {e} ({url})", file=sys.stderr)
            errors += 1
            continue

        if looks_like_passport_block(body):
            print(
                f"{stem}: got Passport York / SSO page instead of timetable (need --cookie from logged-in browser?). {url}",
                file=sys.stderr,
            )
            errors += 1
            continue

        to_write = html_bytes_for_disk(body)
        out_path.write_bytes(to_write)
        print(f"Wrote {len(to_write)} bytes -> {out_path.relative_to(root)}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
