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

When a new download looks empty or much smaller than the existing file on disk (e.g. timetable
not released), the prior HTML is kept and the write is skipped — see PAGE_SOURCE_* env vars in
run_seed_pipeline.py. Use --fail-on-guard-skip or PAGE_SOURCE_FAIL_ON_GUARD_SKIP=1 so the process
exits 3 and a human can review before forcing PAGE_SOURCE_ALLOW_DEGRADED_OVERWRITE=1.

Requires network access to apps1.sis.yorku.ca (no extra pip packages).
"""

from __future__ import annotations

import argparse
import json
import os
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


def _html_utf8_text(disk_bytes: bytes) -> str:
    return disk_bytes.decode("utf-8", errors="replace")


def _html_tr_count(html: str) -> int:
    """Cheap proxy for timetable size (no BeautifulSoup)."""
    return html.lower().count("<tr")


def _looks_like_timetable_placeholder(html: str) -> bool:
    """SIS sometimes serves a stub page when timetables are not released."""
    t = html.lower()
    needles = (
        "not been released",
        "not yet been released",
        "not available at this time",
        "timetable has not",
        "please check back",
        "no courses available",
    )
    return any(n in t for n in needles)


def _cancellation_mention_count(html: str) -> int:
    t = html.lower()
    return (
        t.count("cancelled")
        + t.count("canceled")
        + t.count("cancellation")
        + t.count("cancellations")
    )


def _bypass_preserve_for_cancellations(old_tr: int, new_tr: int, new_html: str) -> bool:
    """
    Large row-count drops are suspicious, but real timetables often mark removals as cancelled.
    If the new HTML has enough cancellation language on a non-tiny page, accept the update.
    """
    if new_tr < 12:
        return False
    mentions = _cancellation_mention_count(new_html)
    if mentions < 8:
        return False
    # Scale with prior size: big timetables may list many cancelled sections.
    if mentions >= max(16, old_tr // 35):
        return True
    # Moderate drop but cancellation wording throughout.
    if new_tr >= old_tr * 0.30 and mentions >= 14:
        return True
    return False


def _default_regression_ratio() -> float:
    # Default 0.55: new file must keep ≥55% of prior <tr> proxy (bias toward not losing data).
    raw = os.environ.get("PAGE_SOURCE_REGRESSION_RATIO", "0.55").strip()
    try:
        r = float(raw)
    except ValueError:
        return 0.55
    if not 0 < r <= 1:
        return 0.55
    return r


def _default_regression_min_prior_tr() -> int:
    raw = os.environ.get("PAGE_SOURCE_REGRESSION_MIN_PRIOR", "70").strip()
    try:
        n = int(raw)
    except ValueError:
        return 70
    return max(0, n)


def _truthy_env(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _allow_degraded_page_source_overwrite() -> bool:
    return _truthy_env("PAGE_SOURCE_ALLOW_DEGRADED_OVERWRITE")


def _should_preserve_prior_page_source(old_tr: int, new_tr: int, new_html: str) -> bool:
    """
    Keep existing on-disk HTML when the new download looks empty or far smaller (<tr> proxy).

    - new has no rows while prior had rows
    - placeholder/stub text and far fewer rows
    - default: new < PAGE_SOURCE_REGRESSION_RATIO (default 0.55) × old, when old has at least
      PAGE_SOURCE_REGRESSION_MIN_PRIOR (default 70) <tr> — catches e.g. full timetable → one course

    Override: PAGE_SOURCE_ALLOW_DEGRADED_OVERWRITE=1, or cancellation-heavy new HTML
    (_bypass_preserve_for_cancellations).
    """
    if old_tr <= 0:
        return False
    if new_tr == 0:
        return True

    if _bypass_preserve_for_cancellations(old_tr, new_tr, new_html):
        return False

    if old_tr >= 30 and _looks_like_timetable_placeholder(new_html) and new_tr < max(15, int(old_tr * 0.25)):
        return True

    min_ratio = _default_regression_ratio()
    min_prior = _default_regression_min_prior_tr()
    if old_tr < min_prior:
        return False
    if new_tr < old_tr * min_ratio:
        return True
    return False


def _maybe_keep_prior_page_source(
    *,
    stem: str,
    out_path: Path,
    incoming_disk_bytes: bytes,
) -> tuple[bool, str]:
    """
    Returns (wrote_incoming, message for log). If False, caller should skip write
    (disk file unchanged).
    """
    if _allow_degraded_page_source_overwrite():
        return True, ""

    if not out_path.is_file():
        return True, ""

    try:
        prior_bytes = out_path.read_bytes()
    except OSError:
        return True, ""

    new_html = _html_utf8_text(incoming_disk_bytes)
    prior_html = _html_utf8_text(prior_bytes)
    old_tr = _html_tr_count(prior_html)
    new_tr = _html_tr_count(new_html)

    if _should_preserve_prior_page_source(old_tr, new_tr, new_html):
        reason = (
            f"[page_source guard] {stem}: keeping prior file "
            f"(prior <tr>≈{old_tr}, new <tr>≈{new_tr}); not overwriting with degraded fetch"
        )
        return False, reason

    return True, ""


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
    p.add_argument(
        "--fail-on-guard-skip",
        action="store_true",
        help="Exit with code 3 if any file was not written because the page_source guard kept prior HTML "
        "(same as PAGE_SOURCE_FAIL_ON_GUARD_SKIP=1). Use in automation so someone must review or force overwrite.",
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
    guard_skips = 0
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
        write_ok, guard_msg = _maybe_keep_prior_page_source(
            stem=stem, out_path=out_path, incoming_disk_bytes=to_write
        )
        if not write_ok:
            guard_skips += 1
            print(guard_msg, file=sys.stderr)
            print(f"Skipped write (prior kept) -> {out_path.relative_to(root)}")
            continue

        out_path.write_bytes(to_write)
        print(f"Wrote {len(to_write)} bytes -> {out_path.relative_to(root)}")

    if guard_skips:
        print(
            f"\npage_source guard: kept prior HTML for {guard_skips} file(s). "
            "To accept the fetched version anyway, re-run with PAGE_SOURCE_ALLOW_DEGRADED_OVERWRITE=1 "
            "or review the new downloads in a browser.",
            file=sys.stderr,
        )

    if errors:
        return 1

    fail_guard = args.fail_on_guard_skip or _truthy_env("PAGE_SOURCE_FAIL_ON_GUARD_SKIP")
    if fail_guard and guard_skips:
        print(
            "Exiting with code 3: fail-on-guard-skip enabled and at least one prior file was preserved.",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
