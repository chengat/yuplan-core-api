#!/usr/bin/env python3
"""
Single entrypoint: fetch SIS HTML → run scrapers → generate db/seed.sql → optionally load DB.

Environment:
  DATABASE_URL          Used by seed.sh when you pass --apply-db (or API does, if DATABASE_URL was set at startup).
  YORK_SIS_COOKIE       Optional fallback for SIS fetch; API usually sends cookie in POST JSON instead.
  SEED_PIPELINE_APPLY_DB  CLI: "1"/"true" or --apply-db to run seed.sh after generating db/seed.sql.

CLI (from repository root):
  python3 scripts/run_seed_pipeline.py
  python3 scripts/run_seed_pipeline.py --cookie '...' --apply-db
  python3 scripts/run_seed_pipeline.py --skip-fetch   # reuse existing page_source HTML
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(cmd: list[str], *, cwd: Path) -> None:
    print("\n+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def truthy_env(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def main() -> int:
    root = repo_root()
    py = sys.executable
    fetch = str(root / "scripts" / "fetch_page_sources.py")
    scrape = str(root / "scraping" / "scrapers" / "scrape.py")
    gen = str(root / "scripts" / "generate_seed.py")
    seed_sh = str(root / "scripts" / "seed.sh")

    default_cookie = os.environ.get("YORK_SIS_COOKIE", "").strip()

    p = argparse.ArgumentParser(
        description="Fetch timetable HTML, scrape JSON, write db/seed.sql, optionally apply to DB."
    )
    p.add_argument(
        "--fw-term",
        default="fall-winter-2026-2027",
        metavar="FOLDER",
        help="page_source / data subfolder for fall-winter",
    )
    p.add_argument(
        "--summer-term",
        default="summer-2026",
        metavar="FOLDER",
        help="page_source subfolder for summer static HTML",
    )
    p.add_argument("--skip-fetch", action="store_true", help="Do not download HTML")
    p.add_argument(
        "--skip-summer-fetch",
        action="store_true",
        help="Only fetch fall/winter HTML (leave summer page_source as-is)",
    )
    p.add_argument("--only", default="", help="Comma-separated stems for fetch_page_sources --only")
    p.add_argument("--fetch-delay", type=float, default=10.0, help="Seconds between fetch requests")
    p.add_argument("--timeout", type=int, default=60, help="HTTP timeout for fetch")
    p.add_argument("--referer", default="https://apps1.sis.yorku.ca/", help="Referer for fetch")
    p.add_argument(
        "--cookie",
        default=default_cookie,
        metavar="STRING",
        help="Cookie header for SIS (default: YORK_SIS_COOKIE env)",
    )
    p.add_argument("--dry-run-fetch", action="store_true", help="Print fetch URLs only")
    p.add_argument(
        "--apply-db",
        action="store_true",
        help="Run scripts/seed.sh after generating db/seed.sql (or set SEED_PIPELINE_APPLY_DB)",
    )
    args = p.parse_args()

    apply_db = args.apply_db or truthy_env("SEED_PIPELINE_APPLY_DB")

    scrape_cwd = root / "scraping" / "scrapers"

    if not args.skip_fetch:
        if not (args.cookie or "").strip() and not args.dry_run_fetch:
            print(
                "Warning: no cookie set (use YORK_SIS_COOKIE or --cookie). "
                "SIS may return Passport York instead of timetables.",
                file=sys.stderr,
            )

        def fetch_cmd(term: str) -> list[str]:
            cmd = [
                py,
                fetch,
                "--term",
                term,
                "--delay",
                str(args.fetch_delay),
                "--timeout",
                str(args.timeout),
                "--referer",
                args.referer,
            ]
            if args.only:
                cmd.extend(["--only", args.only])
            if args.cookie:
                cmd.extend(["--cookie", args.cookie])
            if args.dry_run_fetch:
                cmd.append("--dry-run")
            return cmd

        run_step(fetch_cmd(args.fw_term), cwd=root)
        if not args.skip_summer_fetch:
            run_step(fetch_cmd(args.summer_term), cwd=root)

    run_step(
        [py, scrape, "--fall-winter-term", args.fw_term],
        cwd=scrape_cwd,
    )

    run_step(
        [py, gen, args.fw_term, args.summer_term],
        cwd=root,
    )

    print("\nDone: db/seed.sql regenerated.", flush=True)

    if apply_db:
        if not Path(seed_sh).is_file():
            print(f"Missing {seed_sh}", file=sys.stderr)
            return 1
        run_step(["/bin/bash", seed_sh], cwd=root)
        print("\nDone: database seeded via scripts/seed.sh.", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
